"""(d) POSIX export of a throwaway repository: exec bit, symlinks (also ../..), names differing only by case; through the tool and directly."""
import json
import os
import shutil
import stat
import sys
import tempfile
import time

from lib import git, snapshot, tree_hash
from reprogate.checkout import Checkout
from reprogate.pipeline import evaluate
from tests import helpers as H

tmp = tempfile.mkdtemp(prefix="rg-d5-")
try:
    src = os.path.join(tmp, "src")
    H.make_repo(os.path.join(tmp, "base"))
    shutil.copytree(os.path.join(tmp, "base"), src, ignore=shutil.ignore_patterns(".git"))
    git(src, "init", "-q")
    with open(os.path.join(src, "run.sh"), "w") as f:
        f.write("#!/bin/sh\necho hi\n")
    os.chmod(os.path.join(src, "run.sh"), 0o755)
    with open(os.path.join(src, "plain.txt"), "w") as f:
        f.write("plain\n")
    with open(os.path.join(src, "A.txt"), "w") as f:
        f.write("upper\n")
    with open(os.path.join(src, "a.txt"), "w") as f:
        f.write("lower\n")
    os.symlink("../..", os.path.join(src, "link"))
    os.symlink("plain.txt", os.path.join(src, "filelink"))
    git(src, "add", "-A")
    git(src, "commit", "-q", "-m", "posix")
    sha = git(src, "rev-parse", "HEAD")[1]
    rc, ls, _ = git(src, "ls-tree", "-r", sha)
    modes = {}
    for l in ls.splitlines():
        meta, path = l.split("\t")
        modes[path] = meta.split()[0]
    print("tracked modes:", {k: modes[k] for k in ("run.sh", "plain.txt", "link", "filelink", "A.txt", "a.txt")})
    s0 = snapshot(src)
    t = time.time()
    co = Checkout(src, sha)
    print("export took %.2f s" % (time.time() - t))
    try:
        p = co.path
        print("exec bit run.sh:", bool(os.stat(os.path.join(p, "run.sh")).st_mode & 0o111), "| exec bit plain.txt:", bool(os.stat(os.path.join(p, "plain.txt")).st_mode & 0o111))
        print("link is symlink:", os.path.islink(os.path.join(p, "link")), "target text:", os.readlink(os.path.join(p, "link")))
        print("filelink is symlink:", os.path.islink(os.path.join(p, "filelink")), "target text:", os.readlink(os.path.join(p, "filelink")))
        print("A.txt:", open(os.path.join(p, "A.txt")).read().strip(), "| a.txt:", open(os.path.join(p, "a.txt")).read().strip(), "| listing has both:", {"A.txt", "a.txt"} <= set(os.listdir(p)))
        t = time.time()
        h = tree_hash(p)
        print("tree_hash of the checkout finished in %.2f s (does not recurse through link): %s, files hashed %d" % (time.time() - t, h[0][:16], h[1]))
        print(".git anywhere in checkout:", [r for r, d, f in os.walk(p) if ".git" in d or ".git" in f])
    finally:
        rec = co.finish()
    print("record:", {k: rec[k] for k in ("mode", "files_written", "symlinks_created", "submodules_not_checked_out", "has_git_entry", "cleanup")})
    out = os.path.join(tmp, "ev")
    repro = os.path.join(tmp, "probe.py")
    with open(repro, "w") as f:
        f.write('''import os, minilib
repo = os.path.dirname(os.path.dirname(minilib.__file__))
print("seen_by_reproducer", sorted(os.listdir(repo)))
print("link_is_symlink", os.path.islink(os.path.join(repo, "link")), os.readlink(os.path.join(repo, "link")))
print("exec_bit_run_sh", bool(os.stat(os.path.join(repo, "run.sh")).st_mode & 0o111))
from minilib import Box
Box(2)["a"] = 1
''')
    o = evaluate(src, H.PYTHON, H.verified_claim(), repro, out, checkout_sha=sha, gate=False, runs=3, timeout=30, min_completed=3)
    c = json.load(open(os.path.join(out, "checkout.json")))
    print("through the tool: outcome", o["outcome"], o["outcome_reason"], o["run_status"], "| checkout.json", {k: c[k] for k in ("files_written", "symlinks_created", "cleanup", "has_git_entry")})
    print("reproducer stdout:", open(os.path.join(out, "runs", "run-01", "stdout.txt")).read().strip().replace("\n", " | "))
    s1 = snapshot(src)
    print("SOURCE_IDENTICAL", s0 == s1)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
