import errno
import json
import os
import socket
import time

r = {"pid_uid": os.getuid(), "gid": os.getgid()}
r["env_names_inside"] = sorted(os.environ)
r["canary_visible"] = "REPROGATE_CANARY_SECRET" in os.environ
for line in open("/proc/self/status"):
    if line.startswith(("CapEff", "CapPrm", "CapBnd", "NoNewPrivs")):
        k, v = line.split(":")
        r[k] = v.strip()
r["net_interfaces"] = sorted(os.listdir("/sys/class/net"))
try:
    s = socket.socket()
    s.settimeout(3)
    s.connect(("1.1.1.1", 53))
    r["connect"] = "CONNECTED"
except OSError as e:
    r["connect"] = "FAILED " + errno.errorcode.get(e.errno, str(e.errno))
for name in ("memory.max", "memory.swap.max", "pids.max", "cpu.max", "memory/memory.limit_in_bytes", "memory/memory.memsw.limit_in_bytes",
             "pids/pids.max", "cpu/cpu.cfs_quota_us", "cpu/cpu.cfs_period_us"):
    try:
        r["cgroup_" + name.replace("/", "_")] = open("/sys/fs/cgroup/" + name).read().strip()
    except OSError as e:
        r["cgroup_" + name.replace("/", "_")] = "unreadable " + errno.errorcode.get(e.errno, str(e.errno))
mounts = {}
for line in open("/proc/mounts"):
    f = line.split()
    if f[1] in ("/", "/repo", "/tmp", "/work", "/out", "/rg/harness.py", "/rg/repro.py"):
        mounts[f[1]] = [f[2], [o for o in f[3].split(",") if o in ("ro", "rw", "noexec", "nosuid") or o.startswith("size=")]]
r["mounts"] = mounts


def w(path):
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        os.write(fd, b"x")
        os.close(fd)
        return "WROTE"
    except OSError as e:
        return "FAILED " + errno.errorcode.get(e.errno, str(e.errno))


r["write_/"] = w("/pwned")
r["tmp_marker_present_at_start"] = os.path.exists("/tmp/marker")
r["work_marker_present_at_start"] = os.path.exists("/work/marker")
r["write_/tmp/marker"] = w("/tmp/marker")
r["write_/work/marker"] = w("/work/marker")
r["write_/repo/x"] = w("/repo/x")
r["write_/out/probe-out"] = w("/out/probe-out")
r["hostname"] = socket.gethostname()
print(json.dumps(r, sort_keys=True))
time.sleep(5)
