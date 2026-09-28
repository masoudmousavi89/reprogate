"""Docker sandbox for the reproducer process (F-017).

Isolation per run: no network, read-only root filesystem, repository mounted read-only, all capabilities
dropped, no-new-privileges, non-root user, memory / CPU / pids limits, tmpfs scratch space. The observation
file is written to a small writable mount (/out): the harness still runs in the SAME process as the
reproducer, so observation integrity stays BEST_EFFORT_IN_PROCESS. Docker mode has only been exercised on Linux.
"""
import json
import subprocess
import uuid

DEFAULTS = {"memory": "512m", "cpus": "1", "pids": 128}
LAUNCH_ERROR_CODES = (125, 126, 127)  # docker itself failed / command not found


def make(image, **kw):
    sb = {"kind": "DOCKER", "image": image, "python": "python"}
    sb.update(DEFAULTS)
    sb.update(kw)
    return sb


def new_name():
    return "reprogate-" + uuid.uuid4().hex[:12]


def run_prefix(sb, name, mounts=(), env=None):
    """docker run ... IMAGE  (append the command to run inside)."""
    cmd = ["docker", "run", "--rm", "--name", name, "--network", "none", "--read-only",
           "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
           "--pids-limit", str(sb["pids"]), "--memory", sb["memory"], "--memory-swap", sb["memory"],
           "--cpus", str(sb["cpus"]), "--user", "65534:65534",
           "--tmpfs", "/tmp:rw,size=64m,noexec,nosuid", "--tmpfs", "/work:rw,size=64m,noexec,nosuid",
           "-w", "/work"]
    for k, v in sorted((env or {}).items()):
        cmd += ["-e", "%s=%s" % (k, v)]
    for host, cont, mode in mounts:
        cmd += ["-v", "%s:%s:%s" % (host, cont, mode)]
    cmd.append(sb["image"])
    return cmd


def kill(name):
    try:
        subprocess.run(["docker", "kill", name], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        pass


def image_id(sb):
    try:
        p = subprocess.run(["docker", "image", "inspect", "--format", "{{json .}}", sb["image"]],
                           stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        if p.returncode != 0:
            return None, None
        d = json.loads(p.stdout.decode("utf-8", "replace"))
        return d.get("Id"), d.get("RepoDigests")
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None, None


def record(sb):
    """The `sandbox` object stored in evidence."""
    if sb is None:
        return {"kind": "HOST_PROCESS", "network_isolation": "NONE", "filesystem_isolation": "NONE",
                "note": "prototype host mode: not a sandbox"}
    iid, digests = image_id(sb)
    return {"kind": "DOCKER", "image": sb["image"], "image_id": iid, "repo_digests": digests,
            "network_isolation": "DISABLED", "filesystem_isolation": "READ_ONLY_ROOT_AND_REPO",
            "user": "65534:65534", "cap_drop": "ALL", "no_new_privileges": True,
            "memory": sb["memory"], "cpus": str(sb["cpus"]), "pids_limit": sb["pids"],
            "note": "container isolation; observation still in-process with the reproducer"}
