"""Host-process runner (PROTOTYPE): NO sandbox, NO network isolation. See THREAT_MODEL.md."""
import json
import os
import subprocess
import time

from . import sandbox as sbx
from .util import canonical_json, sha256_bytes, sha256_file

HARNESS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "harness.py")
ENV_KEEP = ("SYSTEMROOT", "SYSTEMDRIVE", "TEMP", "TMP", "PATH", "PATHEXT", "COMSPEC", "LANG", "LC_ALL")
SKIP_DIR_NAMES = {".git", ".hg", ".svn", "__pycache__", ".pytest_cache", ".mypy_cache", ".tox", "node_modules"}
MAX_CAPTURE = 65536


def build_env(seed):
    env = {k: os.environ[k] for k in ENV_KEEP if k in os.environ}
    env.update({
        "PYTHONHASHSEED": str(seed),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONIOENCODING": "utf-8",
    })
    return env


def env_names():
    return sorted(set(ENV_KEEP) | {"PYTHONHASHSEED", "PYTHONDONTWRITEBYTECODE", "PYTHONNOUSERSITE", "PYTHONIOENCODING"})


def _skip_dir(name):
    return name in SKIP_DIR_NAMES or name == "venv" or name.startswith(".venv")


def tree_hash(root):
    """Deterministic hash of all regular files under root (skips VCS, venvs, caches, .pyc)."""
    root = os.path.abspath(root)
    entries = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not _skip_dir(d))
        for name in sorted(filenames):
            if name.endswith((".pyc", ".pyo")) or name == ".git":
                continue
            p = os.path.join(dirpath, name)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            try:
                digest = sha256_file(p)
            except OSError:
                digest = "UNREADABLE"
            entries.append(rel + "\0" + digest)
    return sha256_bytes("\n".join(entries).encode("utf-8")), len(entries)


def _run_small(cmd, timeout=60):
    try:
        p = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=timeout, env=build_env(0))
        return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, "", str(e)


def capture_environment(python, sandbox=None):
    code = ("import sys, json, platform; print(json.dumps({'version': sys.version.split()[0], "
            "'implementation': sys.implementation.name, 'executable': sys.executable, "
            "'system': platform.system()}))")
    def inner(*args):
        if sandbox is None:
            return [python] + list(args)
        return sbx.run_prefix(sandbox, sbx.new_name()) + [sandbox["python"]] + list(args)

    rc, out, err = _run_small(inner("-c", code), timeout=120 if sandbox else 60)
    info = {"python": None, "packages": None, "errors": []}
    if rc == 0:
        info["python"] = json.loads(out)
    else:
        info["errors"].append("cannot run interpreter: " + err.strip()[:300])
        return info, None
    rc, out, err = _run_small(inner("-m", "pip", "list", "--format=json", "--disable-pip-version-check"),
                              timeout=120 if sandbox else 60)
    if rc == 0:
        try:
            pk = json.loads(out)
            info["packages"] = sorted([p["name"].lower(), p["version"]] for p in pk)
        except ValueError:
            info["errors"].append("pip list returned invalid JSON")
    else:
        info["errors"].append("pip list failed: " + err.strip()[:300])
    fp = {"python_version": info["python"]["version"], "implementation": info["python"]["implementation"],
          "packages": info["packages"]}
    if sandbox is not None:
        fp["image_id"] = sbx.image_id(sandbox)[0]
    return info, sha256_bytes(canonical_json(fp).encode("utf-8"))


def git_info(repo):
    def git(*args):
        return _run_small(["git", "-C", repo] + list(args), timeout=30)

    rc, out, _ = git("rev-parse", "HEAD")
    info = {"commit": out.strip() if rc == 0 else None, "dirty_tracked_files": None}
    if rc == 0:
        rc2, out2, _ = git("status", "--porcelain", "--untracked-files=no")
        if rc2 == 0:
            info["dirty_tracked_files"] = len([l for l in out2.splitlines() if l.strip()])
    return info


def _group_kwargs():
    if os.name == "nt":
        return {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
    return {"start_new_session": True}


def _kill_tree(popen):
    """Kill the harness and its worker (the supervisor/worker split has two processes)."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(popen.pid)], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=30)
        else:
            import signal
            os.killpg(popen.pid, signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        popen.kill()
    except OSError:
        pass


def _clip(b):
    return b[:MAX_CAPTURE] if b else b""


def run_once(python, repo, repro_bytes, run_dir, timeout, seed, pythonpath_extra=None, sandbox=None):
    """Execute the harness once in a fresh process. Returns a raw result dict."""
    work = os.path.join(run_dir, "work")
    rdir = os.path.join(run_dir, "repro")
    os.makedirs(work, exist_ok=True)
    os.makedirs(rdir, exist_ok=True)
    repro_copy = os.path.join(rdir, "repro.py")
    with open(repro_copy, "wb") as f:
        f.write(repro_bytes)
    obs_path = os.path.join(run_dir, "observation.json")
    container = None
    if sandbox is None:
        cmd = [python, HARNESS, "--repo", os.path.abspath(repo), "--repro", repro_copy, "--out", obs_path]
        popen_env = build_env(seed)
        popen_cwd = work
    else:
        out_dir = os.path.join(run_dir, "out")
        os.makedirs(out_dir, exist_ok=True)
        os.chmod(out_dir, 0o777)  # the container user (65534) must be able to write the observation
        obs_path = os.path.join(out_dir, "observation.json")
        container = sbx.new_name()
        cenv = {k: v for k, v in build_env(seed).items() if k.startswith("PYTHON")}
        mounts = [(os.path.abspath(repo), "/repo", "ro"), (HARNESS, "/rg/harness.py", "ro"),
                  (repro_copy, "/rg/repro.py", "ro"), (out_dir, "/out", "rw")]
        cmd = sbx.run_prefix(sandbox, container, mounts, cenv) + [
            sandbox["python"], "/rg/harness.py", "--repo", "/repo", "--repro", "/rg/repro.py",
            "--out", "/out/observation.json"]
        popen_env = build_env(seed)
        popen_cwd = None
    for e in pythonpath_extra or []:
        cmd += ["--pythonpath-extra", e]
    res = {"seed": seed, "timed_out": False, "launch_error": None, "returncode": None,
           "stdout": b"", "stderr": b"", "observation": None, "observation_error": None}
    start = time.time()
    try:
        popen = subprocess.Popen(cmd, cwd=popen_cwd, env=popen_env, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, **_group_kwargs())
        try:
            out, err = popen.communicate(timeout=timeout)
            res["returncode"], res["stdout"], res["stderr"] = popen.returncode, out, err
            if container and popen.returncode in sbx.LAUNCH_ERROR_CODES and not os.path.exists(obs_path):
                res["launch_error"] = "docker: " + err.decode("utf-8", "replace").strip()[:300]
        except subprocess.TimeoutExpired:
            res["timed_out"] = True
            if container:
                sbx.kill(container)
            _kill_tree(popen)
            out, err = popen.communicate()
            res["stdout"], res["stderr"] = out or b"", err or b""
    except OSError as e:
        res["launch_error"] = str(e)
    res["duration_s"] = round(time.time() - start, 3)
    if os.path.exists(obs_path):
        try:
            with open(obs_path, "r", encoding="utf-8") as f:
                doc = json.load(f)
            if res["returncode"] != 0 and not res["timed_out"]:
                # the supervisor always exits 0 after writing the file; anything else means the file is not its work
                res["observation_error"] = "harness exited with code %r; observation file not trusted" % res["returncode"]
            elif "observation_error" in doc:
                res["observation_error"] = doc["observation_error"]
            else:
                res["observation"] = doc
        except (OSError, ValueError) as e:
            res["observation_error"] = str(e)
    else:
        res["observation_error"] = "observation file missing"
    with open(os.path.join(run_dir, "stdout.txt"), "wb") as f:
        f.write(_clip(res["stdout"]))
    with open(os.path.join(run_dir, "stderr.txt"), "wb") as f:
        f.write(_clip(res["stderr"]))
    return res
