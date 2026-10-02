"""(f) the worktree equals `git archive` of the same SHA, byte for byte (content, executable bit, file list)."""
import os
import subprocess
import sys
import tarfile
import tempfile
import shutil

from lib import tree_hash
from reprogate.checkout import Checkout

src = sys.argv[1]
for sha in ("81825095d24f4dbccb40f787fff70db54989b91c", "9a7dd7b28b50fd8adc019ab2702b50ae5c6ed782"):
    tmp = tempfile.mkdtemp(prefix="rg-f-")
    co = Checkout(src, sha)
    try:
        arch = os.path.join(tmp, "archive")
        os.makedirs(arch)
        tar = subprocess.run(["git", "-C", src, "archive", sha], stdout=subprocess.PIPE).stdout
        with open(os.path.join(tmp, "a.tar"), "wb") as f:
            f.write(tar)
        with tarfile.open(os.path.join(tmp, "a.tar")) as t:
            t.extractall(arch)

        def listing(root):
            d = {}
            for dp, dn, fn in os.walk(root):
                dn[:] = [x for x in dn if x != ".git"]
                for n in fn:
                    p = os.path.join(dp, n)
                    rel = os.path.relpath(p, root)
                    if os.path.islink(p):
                        d[rel] = ("L", os.readlink(p))
                    else:
                        with open(p, "rb") as f:
                            d[rel] = ("F", os.stat(p).st_mode & 0o111 != 0, f.read())
            return d
        a, b = listing(co.path), listing(arch)
        diff = sorted(set(a) ^ set(b)) + sorted(k for k in set(a) & set(b) if a[k] != b[k])
        print(sha[:8], "files worktree", len(a), "archive", len(b), "| differences", len(diff), diff[:5],
              "| tree_hash equal", tree_hash(co.path)[0] == tree_hash(arch)[0], tree_hash(arch)[0][:16])
        d = subprocess.run(["diff", "-r", "-q", "--exclude=.git", co.path, arch], stdout=subprocess.PIPE).returncode
        print("  diff -r -q (excluding .git) exit code", d)
    finally:
        co.finish()
        shutil.rmtree(tmp, ignore_errors=True)
