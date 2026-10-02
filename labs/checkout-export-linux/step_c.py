"""(c) /work and the other clauses: one real run through the tool (Docker mode, 3 runs), docker inspect of every container, compared with the previous session's inspect output."""
import json
import os
import re
import subprocess
import sys
import threading
import time

from lib import mask
from reprogate import sandbox as sbx
from reprogate.pipeline import evaluate
from reprogate.runner import env_names

src, image, outdir, inspect_out, previous = sys.argv[1:6]
B = "81825095d24f4dbccb40f787fff70db54989b91c"
os.environ["REPROGATE_CANARY_SECRET"] = "canary-not-a-real-secret"
claim = json.load(open("labs/jinja-843/claim.json"))
result = {}


def runit():
    # gate=False: the probe uses socket and time.sleep, which the real gate does not accept; the gate itself is not changed
    result["o"] = evaluate(src, "python", claim, "labs/checkout-export-linux/probe_env.py", outdir, checkout_sha=B, gate=False,
                           allow_unverified_provenance=True, runs=3, timeout=60, min_completed=3, sandbox=sbx.make(image))


t = threading.Thread(target=runit)
t.start()
seen = {}
while t.is_alive():
    p = subprocess.run(["docker", "ps", "--no-trunc", "--filter", "name=reprogate-", "--format", "{{.ID}} {{.Names}}"], stdout=subprocess.PIPE,
                       stderr=subprocess.DEVNULL)
    for line in p.stdout.decode().splitlines():
        cid, name = line.split()
        if cid not in seen:
            seen[cid] = json.loads(subprocess.run(["docker", "inspect", cid], stdout=subprocess.PIPE).stdout)[0]
    time.sleep(0.2)
t.join()
o = result["o"]
FIELDS = ("NetworkMode", "ReadonlyRootfs", "CapDrop", "CapAdd", "SecurityOpt", "PidsLimit", "Memory", "MemorySwap", "NanoCpus", "Tmpfs", "Binds",
          "AutoRemove", "Privileged", "PublishAllPorts")
keep = []
for cid, d in seen.items():
    h = d["HostConfig"]
    keep.append({"Id": cid, "Name": d["Name"], "Image": d["Config"]["Image"], "User": d["Config"]["User"], "WorkingDir": d["Config"]["WorkingDir"],
                 "Env_names": sorted(e.split("=", 1)[0] for e in d["Config"]["Env"]),
                 "HostConfig": {k: h.get(k) for k in FIELDS},
                 "Mounts": [{"Type": m["Type"], "Source": m["Source"], "Destination": m["Destination"], "RW": m["RW"]} for m in d["Mounts"]]})
text = mask(json.dumps(keep, indent=1, sort_keys=True))
text = re.sub(r"/[^\"]*?/reprogate-checkout-[^/\"]+", "<CHECKOUT_TMP>", text)
text = re.sub(r"/[^\"]*?/runs/run-0\d", "<EVIDENCE>/runs/run-0N", text)
text = text.replace(os.getcwd(), "<REPO>")
open(inspect_out, "w").write(text + "\n")
print("containers seen by docker inspect:", len(keep), "distinct ids:", len({k["Id"] for k in keep}), "distinct names:", len({k["Name"] for k in keep}))


def shape(k):
    h = dict(k["HostConfig"])
    h["Binds"] = sorted(re.sub(r"^.*?:/", "/", b) for b in (h["Binds"] or []))
    tm = dict(h["Tmpfs"] or {})
    h["Tmpfs"] = tm
    return {"User": k["User"], "Env_names": k["Env_names"], "WorkingDir": k["WorkingDir"], **h}


prev = json.load(open(previous))
prev_shapes = [shape(k) for k in prev]
for k in keep:
    s = shape(k)
    tm = s["Tmpfs"]
    s_cmp = dict(s)
    s_cmp["Tmpfs"] = {p: v.replace(",mode=1777", "") if p == "/work" else v for p, v in tm.items()}
    same_as_prev = any(s_cmp == ps for ps in prev_shapes)
    print(" ", k["Name"], "Tmpfs", tm, "| binds", s["Binds"], "| all other fields equal a container of the previous inspect (after removing mode=1777 from /work):", same_as_prev)
    if not same_as_prev:
        for ps in prev_shapes[:1]:
            print("    differing keys vs previous:", sorted(x for x in s_cmp if s_cmp[x] != ps.get(x)))
h = keep[-1]["HostConfig"]
print("one container:", {k: h[k] for k in ("NetworkMode", "ReadonlyRootfs", "CapDrop", "SecurityOpt", "PidsLimit", "Memory", "MemorySwap", "NanoCpus", "AutoRemove", "Privileged")}, "user", keep[-1]["User"])
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
    print("run %d: uid %s NoNewPrivs %s CapEff %s net %s connect %s" % (i, r["pid_uid"], r.get("NoNewPrivs"), r.get("CapEff"), r["net_interfaces"], r["connect"]))
    print("   cwd", r["cwd"], "| /work mode", r["stat_/work_mode"], "| /tmp mode", r["stat_/tmp_mode"], "| mounts /work", r["mounts"].get("/work"))
    print("   writes", {k: v for k, v in r.items() if k.startswith("write_")})
    print("   markers present at start: /tmp", r["tmp_marker_present_at_start"], "/work", r["work_marker_present_at_start"], "| canary visible", r["canary_visible"])
    print("   cgroup limits", {k[7:]: v for k, v in r.items() if k.startswith("cgroup_") and not v.startswith("unreadable")})
if env0:
    print("env names inside:", env0)
    print("inside but not in env_names():", sorted(set(env0) - set(env_names())))
ps = subprocess.run(["docker", "ps", "-a", "--filter", "name=reprogate-", "--format", "{{.Names}}"], stdout=subprocess.PIPE).stdout.decode().split()
print("containers left after the run:", len(ps))
