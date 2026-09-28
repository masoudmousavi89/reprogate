"""Host-process runner (PROTOTYPE): NO sandbox, NO network isolation. See THREAT_MODEL.md."""
import json
import os
import subprocess
import time

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


def capture_environment(python):
    code = ("import sys, json, platform; print(json.dumps({'version': sys.version.split()[0], "
            "'implementation': sys.implementation.name, 'executable': sys.executable, "
            "'system': platform.system()}))")
    rc, out, err = _run_small([python, "-c", code])
    info = {"python": None, "packages": None, "errors": []}
    if rc == 0:
        info["python"] = json.loads(out)
    else:
        info["errors"].append("cannot run interpreter: " + err.strip()[:300])
        return info, None
    rc, out, err = _run_small([python, "-m", "pip", "list", "--format=json", "--disable-pip-version-check"])
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


def _clip(b):
    return b[:MAX_CAPTURE] if b else b""


def run_once(python, repo, repro_bytes, run_dir, timeout, seed, pythonpath_extra=None):
    """Execute the harness once in a fresh process. Returns a raw result dict."""
    work = os.path.join(run_dir, "work")
    rdir = os.path.join(run_dir, "repro")
    os.makedirs(work, exist_ok=True)
    os.makedirs(rdir, exist_ok=True)
    repro_copy = os.path.join(rdir, "repro.py")
    with open(repro_copy, "wb") as f:
        f.write(repro_bytes)
    obs_path = os.path.join(run_dir, "observation.json")
    cmd = [python, HARNESS, "--repo", os.path.abspath(repo), "--repro", repro_copy, "--out", obs_path]
    for e in pythonpath_extra or []:
        cmd += ["--pythonpath-extra", e]
    res = {"seed": seed, "timed_out": False, "launch_error": None, "returncode": None,
           "stdout": b"", "stderr": b"", "observation": None, "observation_error": None}
    start = time.time()
    try:
        p = subprocess.run(cmd, cwd=work, env=build_env(seed), stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        res["returncode"], res["stdout"], res["stderr"] = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        res["timed_out"] = True
        res["stdout"], res["stderr"] = e.stdout or b"", e.stderr or b""
    except OSError as e:
        res["launch_error"] = str(e)
    res["duration_s"] = round(time.time() - start, 3)
    if os.path.exists(obs_path):
        try:
            with open(obs_path, "r", encoding="utf-8") as f:
                res["observation"] = json.load(f)
        except (OSError, ValueError) as e:
            res["observation_error"] = str(e)
    else:
        res["observation_error"] = "observation file missing"
    with open(os.path.join(run_dir, "stdout.txt"), "wb") as f:
        f.write(_clip(res["stdout"]))
    with open(os.path.join(run_dir, "stderr.txt"), "wb") as f:
        f.write(_clip(res["stderr"]))
    return res
