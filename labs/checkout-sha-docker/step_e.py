"""(e) one consolidated run through the real tool, Docker mode, 3 runs; docker inspect of every container taken while it runs."""
import json
import os
import subprocess
import sys
import tempfile
import threading
import time

from lib import mask
from reprogate import sandbox as sbx
from reprogate.pipeline import evaluate
from reprogate.runner import env_names

src, image, outdir, inspect_out = sys.argv[1:5]
B = "81825095d24f4dbccb40f787fff70db54989b91c"
os.environ["REPROGATE_CANARY_SECRET"] = "canary-not-a-real-secret"
claim = json.load(open("labs/jinja-843/claim.json"))
result = {}


def runit():
    # gate=False: the probe uses socket and time.sleep, which the real gate does not accept; the gate itself is not changed
    result["o"] = evaluate(src, "python", claim, "labs/checkout-sha-docker/probe_env.py", outdir, checkout_sha=B, gate=False,
                           allow_unverified_provenance=True, runs=3, timeout=60, min_completed=3, sandbox=sbx.make(image))


t = threading.Thread(target=runit)
t.start()
seen = {}
while t.is_alive():
    p = subprocess.run(["docker", "ps", "--no-trunc", "--filter", "name=reprogate-", "--format", "{{.ID}} {{.Names}}"],
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    for line in p.stdout.decode().splitlines():
        cid, name = line.split()
        if cid not in seen:
            d = json.loads(subprocess.run(["docker", "inspect", cid], stdout=subprocess.PIPE).stdout)[0]
            seen[cid] = d
    time.sleep(0.2)
t.join()
o = result["o"]
keep = []
for cid, d in seen.items():
    h = d["HostConfig"]
    keep.append({"Id": cid, "Name": d["Name"], "Image": d["Config"]["Image"], "User": d["Config"]["User"], "WorkingDir": d["Config"]["WorkingDir"],
                 "Env_names": sorted(e.split("=", 1)[0] for e in d["Config"]["Env"]),
                 "HostConfig": {k: h.get(k) for k in ("NetworkMode", "ReadonlyRootfs", "CapDrop", "CapAdd", "SecurityOpt", "PidsLimit", "Memory",
                                                       "MemorySwap", "NanoCpus", "Tmpfs", "Binds", "AutoRemove", "Privileged", "PublishAllPorts")},
                 "Mounts": [{"Type": m["Type"], "Source": m["Source"], "Destination": m["Destination"], "RW": m["RW"]} for m in d["Mounts"]]})
text = mask(json.dumps(keep, indent=1, sort_keys=True))
import re
text = re.sub(r"/[^\"]*?/reprogate-checkout-[^/\"]+", "<CHECKOUT_TMP>", text)
text = re.sub(r"/[^\"]*?/runs/run-0\d", "<EVIDENCE>/runs/run-0N", text)
open(inspect_out, "w").write(text + "\n")
print("containers seen by docker inspect:", len(keep), "distinct ids:", len({k["Id"] for k in keep}), "distinct names:", len({k["Name"] for k in keep}))
for k in keep:
    h = k["HostConfig"]
    print(" ", k["Name"], "network", h["NetworkMode"], "ro_root", h["ReadonlyRootfs"], "CapDrop", h["CapDrop"], "CapAdd", h["CapAdd"], "secopt", h["SecurityOpt"],
          "user", k["User"], "mem", h["Memory"], "swap", h["MemorySwap"], "nanocpus", h["NanoCpus"], "pids", h["PidsLimit"], "autoremove", h["AutoRemove"],
          "privileged", h["Privileged"])
    print("    tmpfs", h["Tmpfs"], "| binds", [mask(b).split("/")[-1] if False else re.sub(r"^.*?:/", "/", b) for b in h["Binds"]])
print("outcome", o["outcome"], o["outcome_reason"], "run_status", o["run_status"], "counts", o["counts"])
env0 = None
for i in (1, 2, 3):
    out = open(os.path.join(outdir, "runs", "run-0%d" % i, "stdout.txt")).read().strip()
    try:
        r = json.loads(out.splitlines()[0])
    except Exception:
        print("run", i, "stdout not JSON:", out[:200])
        continue
    env0 = env0 or r["env_names_inside"]
    print("run %d: uid %s gid %s NoNewPrivs %s CapEff %s CapBnd %s net %s connect %s hostname %s" % (
        i, r["pid_uid"], r["gid"], r.get("NoNewPrivs"), r.get("CapEff"), r.get("CapBnd"), r["net_interfaces"], r["connect"], r["hostname"]))
    print("   cgroup", {k: v for k, v in r.items() if k.startswith("cgroup_")})
    print("   mounts", r["mounts"])
    print("   writes", {k: v for k, v in r.items() if k.startswith("write_")}, "| markers present at start: tmp", r["tmp_marker_present_at_start"], "work", r["work_marker_present_at_start"], "| canary visible", r["canary_visible"])
if env0:
    allowed = set(env_names())
    print("env names inside the container:", env0)
    print("env_names() of runner.py:", sorted(allowed))
    print("inside but not in env_names():", sorted(set(env0) - allowed))
    print("env_names() not inside:", sorted(allowed - set(env0)))
env = json.load(open(os.path.join(outdir, "environment.json")))
print("tree hash before:", env["repository_tree_sha256_before"][:16], "| outcome repository keys:", {k: v for k, v in o.get("repository", {}).items() if "tree" in k or "dirty" in k})
ps = subprocess.run(["docker", "ps", "-a", "--filter", "name=reprogate-", "--format", "{{.Names}}"], stdout=subprocess.PIPE).stdout.decode().split()
print("containers left after the run:", len(ps))
