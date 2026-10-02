"""(a) oracle from two SHAs in Docker mode on the jinja clone; source repository snapshot before and after."""
import json
import os
import subprocess
import sys

from lib import snapshot, mask

src, image, py = sys.argv[1], sys.argv[2], sys.executable
B, A = "81825095d24f4dbccb40f787fff70db54989b91c", "9a7dd7b28b50fd8adc019ab2702b50ae5c6ed782"
out = sys.argv[3]
s0 = snapshot(src)
p = subprocess.run([py, "-m", "reprogate", "oracle", "--before-repo", src, "--after-repo", src, "--before-sha", B,
                    "--after-sha", A, "--claim", "labs/jinja-843/claim.json", "--reproducer", "labs/jinja-843/repro.py",
                    "--out", out, "--sandbox", "docker", "--image", image, "--allow-unverified-provenance"],
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print(mask("\n".join(p.stdout.decode().splitlines()[-4:])))
print("oracle exit code", p.returncode)
s1 = snapshot(src)
for side in ("before", "after"):
    o = json.load(open(os.path.join(out, side, "outcome.json")))
    c = json.load(open(os.path.join(out, side, "checkout.json")))
    print(side, o["outcome"], o["outcome_reason"], o.get("outcome_qualifier"), "counts", o["counts"], "sandbox", o["sandbox"]["kind"])
    print("  checkout.json", {k: c[k] for k in ("requested_sha", "head_sha", "cleanup", "source_worktrees_before", "source_worktrees_after")},
          "source_head_unchanged", c["source_head_before"] == c["source_head_after"])
    e = json.load(open(os.path.join(out, side, "environment.json")))
    print("  environment git.commit", e["git"]["commit"], "tree", e["repository_tree_sha256_before"][:16])
print("source before", {k: (v if k != "refs" else len(v)) for k, v in s0.items()})
print("source after ", {k: (v if k != "refs" else len(v)) for k, v in s1.items()})
print("SOURCE_IDENTICAL", s0 == s1)
