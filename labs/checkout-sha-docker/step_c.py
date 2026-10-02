"""(c) write attempts into /repo, /repo/.git and the host path named in the .git file, through the real tool (real gate), Docker mode."""
import json
import os
import subprocess
import sys

from lib import snapshot, mask

src, image, out = sys.argv[1], sys.argv[2], sys.argv[3]
B = "81825095d24f4dbccb40f787fff70db54989b91c"
s0 = snapshot(src)
p = subprocess.run([sys.executable, "-m", "reprogate", "run", "--repo", src, "--checkout-sha", B, "--claim", "labs/jinja-843/claim.json",
                    "--reproducer", "labs/checkout-sha-docker/probe_write.py", "--out", out, "--sandbox", "docker", "--image", image,
                    "--allow-unverified-provenance"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print(mask("\n".join(p.stdout.decode().splitlines()[-3:])), "| exit", p.returncode)
o = json.load(open(os.path.join(out, "outcome.json")))
print("outcome", o["outcome"], o["outcome_reason"], "gate", json.load(open(os.path.join(out, "gate.json")))["status"], "counts", o["counts"])
print(mask(open(os.path.join(out, "runs", "run-01", "stdout.txt")).read()).replace("/repo", "/repo"))
c = json.load(open(os.path.join(out, "checkout.json")))
print("checkout.json cleanup", c["cleanup"], "worktrees", c["source_worktrees_before"], "->", c["source_worktrees_after"])
s1 = snapshot(src)
print("SOURCE_IDENTICAL", s0 == s1, "(tree, whole .git, HEAD, refs, worktree count)")
