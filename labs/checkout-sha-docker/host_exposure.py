"""(d) host mode: what a reproducer can reach through the worktree's .git file; (d-docker) the same reproducers in Docker mode.
Throwaway local repository built from tests/helpers.py (read-only use). The real gate is NOT changed: evaluate(gate=False) is the pattern of
tests/test_end_to_end.py; the script also reports what the real gate says about each reproducer."""
import json
import os
import shutil
import sys
import tempfile

from lib import git, snapshot, mask
from reprogate import sandbox as sbx
from reprogate.checkout import Checkout
from reprogate.gate import gate_source
from reprogate.pipeline import evaluate
from tests import helpers as H

image = sys.argv[1] if len(sys.argv) > 1 else "mirror.gcr.io/library/python:3.8-slim"
FAST = dict(runs=3, timeout=30, min_completed=3)

HEAD_ = '''import os, minilib
repo = os.path.dirname(os.path.dirname(minilib.__file__))
with open(os.path.join(repo, ".git"), "rb") as f:
    gitdir = f.read().decode().split("gitdir:", 1)[1].strip()
print("gitdir", gitdir, "exists", os.path.exists(gitdir))
def w(tag, path, flags, data=b"x"):
    try:
        fd = os.open(path, flags); os.write(fd, data); os.close(fd); print(tag, "WROTE", path)
    except OSError as e:
        print(tag, "FAILED", e.errno, path)
'''
D1 = HEAD_ + '''w("d1_append_to_worktree_metadata_HEAD", os.path.join(gitdir, "HEAD"), os.O_WRONLY | os.O_APPEND, b"\\n# d1\\n")
from minilib import Box
Box(2)["a"] = 1
'''
D2 = HEAD_ + '''with open(os.path.join(gitdir, "HEAD"), "rb") as f:
    sha = f.read().decode().strip()
common = os.path.normpath(os.path.join(gitdir, "..", ".."))
w("d2_create_ref_in_source_git", os.path.join(common, "refs", "heads", "pwned"), os.O_WRONLY | os.O_CREAT, (sha + "\\n").encode())
from minilib import Box
Box(2)["a"] = 1
'''
D3 = HEAD_ + '''common = os.path.normpath(os.path.join(gitdir, "..", ".."))
OTHER = "%s"
p = os.path.join(common, "objects", OTHER[:2], OTHER[2:])
try:
    os.remove(p); print("d3_unlink_loose_object WROTE", p)
except OSError as e:
    print("d3_unlink_loose_object FAILED", e.errno, p)
from minilib import Box
Box(2)["a"] = 1
'''


def make_src(tmp):
    src = os.path.join(tmp, "src")
    os.makedirs(src)
    git(src, "init", "-q")
    H.make_repo(os.path.join(tmp, "buggy_tmp"))
    for r, _, fs in os.walk(os.path.join(tmp, "buggy_tmp")):
        for n in fs:
            rel = os.path.relpath(os.path.join(r, n), os.path.join(tmp, "buggy_tmp"))
            if rel.startswith(".git"):
                continue
            os.makedirs(os.path.dirname(os.path.join(src, rel)), exist_ok=True)
            shutil.copyfile(os.path.join(r, n), os.path.join(src, rel))
    git(src, "add", "-A"); git(src, "commit", "-q", "-m", "buggy")
    buggy = git(src, "rev-parse", "HEAD")[1]
    H.make_repo(os.path.join(tmp, "fixed_tmp"), fixed=True)
    shutil.copyfile(os.path.join(tmp, "fixed_tmp", "minilib", "box.py"), os.path.join(src, "minilib", "box.py"))
    git(src, "commit", "-q", "-a", "-m", "fix")
    fixed = git(src, "rev-parse", "HEAD")[1]
    return src, buggy, fixed


def attack(name, template, mode):
    tmp = tempfile.mkdtemp(prefix="rg-d-")
    try:
        src, buggy, fixed = make_src(tmp)
        code = template % fixed if "%s" in template else template
        rp = os.path.join(tmp, name + ".py")
        with open(rp, "w") as f:
            f.write(code)
        s0 = snapshot(src)
        kw = dict(FAST)
        if mode == "docker":
            kw.update(sandbox=sbx.make(image))
            py = "python"
        else:
            py = H.PYTHON
        g = gate_source(code.encode())["status"]
        out = os.path.join(tmp, "ev")
        o = evaluate(src, py, H.verified_claim(), rp, out, checkout_sha=buggy, gate=False, **kw)
        stdout = open(os.path.join(out, "runs", "run-01", "stdout.txt")).read()
        c = json.load(open(os.path.join(out, "checkout.json")))
        s1 = snapshot(src)
        print("=== %s [%s]" % (name, mode))
        print("real gate on this reproducer:", g)
        print("reproducer stdout (run 1):", mask(stdout.strip()).replace(src, "<SRC>").replace(tmp, "<TMP>"))
        print("outcome", o["outcome"], o["outcome_reason"], "run_status", o["run_status"])
        print("checkout.json cleanup", c["cleanup"], "worktrees", c["source_worktrees_before"], "->", c["source_worktrees_after"],
              "| source_head unchanged", c["source_head_before"] == c["source_head_after"])
        print("source tree hash unchanged", s0["tree_sha256"] == s1["tree_sha256"], "| whole .git unchanged", s0["git_dir_sha256"] == s1["git_dir_sha256"],
              "| refs before/after", len(s0["refs"]), len(s1["refs"]))
        if s0["refs"] != s1["refs"]:
            print("  new refs:", sorted(set(s1["refs"]) - set(s0["refs"])))
        rc, fsck, ferr = git(src, "fsck", "--no-dangling")
        print("git fsck of the source: rc", rc, "|", mask((fsck + " " + ferr).replace(tmp, "<TMP>"))[:300].replace("\n", " ; "))
        rc, t, err = git(src, "cat-file", "-t", fixed)
        print("cat-file -t <fixed commit>: rc", rc, t or err[:120])
        try:
            Checkout(src, fixed).finish()
            print("later Checkout(source, <fixed commit>): OK")
        except ValueError as e:
            print("later Checkout(source, <fixed commit>): ValueError:", str(e)[:140].replace(tmp, "<TMP>"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


for mode in ("host", "docker"):
    for name, t in (("d1", D1), ("d2", D2), ("d3", D3)):
        attack(name, t, mode)
