"""(b) oracle from two SHAs in Docker mode; tree hashes against the Windows references; export time; source snapshot before and after."""
import json
import os
import subprocess
import sys
import time

from lib import snapshot, mask
from reprogate.checkout import Checkout

src, image, out = sys.argv[1], sys.argv[2], sys.argv[3]
B, A = "81825095d24f4dbccb40f787fff70db54989b91c", "9a7dd7b28b50fd8adc019ab2702b50ae5c6ed782"
REF = {"before": "dbc9cd7de8574222da889f9f94b65d4fd5054e50f4a09128da7b90f10d983b06",
       "after": "bf8ae6f92378232b5eb2275a763eda0e8ce40ba5766f0b02ffa535d130fee973"}
for sha in (B, A):
    t = time.time()
    co = Checkout(src, sha)
    dt = time.time() - t
    print("export of", sha[:8], "took %.2f s, files_written %d" % (dt, co.files_written))
    co.finish()
s0 = snapshot(src)
p = subprocess.run([sys.executable, "-m", "reprogate", "oracle", "--before-repo", src, "--after-repo", src, "--before-sha", B, "--after-sha", A,
                    "--claim", "labs/jinja-843/claim.json", "--reproducer", "labs/jinja-843/repro.py", "--out", out, "--sandbox", "docker",
                    "--image", image, "--allow-unverified-provenance"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print(mask("\n".join(p.stdout.decode().splitlines()[-4:])), "| exit", p.returncode)
for side in ("before", "after"):
    o = json.load(open(os.path.join(out, side, "outcome.json")))
    c = json.load(open(os.path.join(out, side, "checkout.json")))
    e = json.load(open(os.path.join(out, side, "environment.json")))
    print(side, o["outcome"], o["outcome_reason"], o.get("outcome_qualifier"), "counts", o["counts"], "sandbox", o["sandbox"]["kind"])
    print("  checkout.json", {k: c[k] for k in ("mode", "requested_sha", "head_sha", "files_written", "symlinks_created", "submodules_not_checked_out",
                                               "blobs_verified", "has_git_entry", "cleanup")}, "source_head_unchanged", c["source_head_before"] == c["source_head_after"])
    h = e["repository_tree_sha256_before"]
    print("  tree hash", h[:16], "equals Windows reference:", h == REF[side], "| git.commit", e["git"]["commit"][:8], "dirty", e["git"].get("dirty_tracked_files"))
s1 = snapshot(src)
print("SOURCE_IDENTICAL", s0 == s1, "(tree, whole .git, HEAD, refs, worktree count)")
