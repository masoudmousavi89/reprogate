"""Checkout of an exact SHA without .git (req_005, decision_079, labs/checkout-export/PREDICTIONS.md)."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

from reprogate import constants as C
from reprogate.checkout import Checkout, safe_relpath
from reprogate.pipeline import evaluate
from reprogate.runner import tree_hash
from tests import helpers as H

FAST = dict(runs=3, timeout=30, min_completed=3)


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.autocrlf=false"]
                       + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.stdout.decode().strip()


def write(path, text, binary=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb" if binary else "w", newline=None if binary else "") as f:
        f.write(text)


def git_dir_hash(repo):
    """Hash of every file under the source .git (names and bytes)."""
    return tree_hash_raw(os.path.join(repo, ".git"))


def tree_hash_raw(root):
    import hashlib
    h = hashlib.sha256()
    for dp, dn, fn in os.walk(root):
        dn.sort()
        for name in sorted(fn):
            p = os.path.join(dp, name)
            h.update(os.path.relpath(p, root).encode() + b"\0")
            with open(p, "rb") as f:
                h.update(f.read())
    return h.hexdigest()


class CheckoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rg-co-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.src = os.path.join(self.tmp, "src")
        os.makedirs(self.src)
        git(self.src, "init", "-q")
        write(os.path.join(self.src, "a.txt"), b"one\r\ntwo\n", binary=True)  # CRLF bytes that were committed
        write(os.path.join(self.src, "sub", "b.txt"), "b\n")
        write(os.path.join(self.src, "ignored.txt"), "must still be exported\n")
        write(os.path.join(self.src, ".gitattributes"), "ignored.txt export-ignore\n*.txt text eol=crlf\n")
        git(self.src, "add", "-A")
        git(self.src, "commit", "-q", "-m", "c1")
        self.c1 = git(self.src, "rev-parse", "HEAD")
        write(os.path.join(self.src, "a.txt"), "two\n")
        git(self.src, "commit", "-q", "-a", "-m", "c2")
        self.c2 = git(self.src, "rev-parse", "HEAD")
        git(self.src, "tag", "v1", self.c1)
        git(self.src, "branch", "side", self.c1)

    def worktrees(self):
        return git(self.src, "worktree", "list", "--porcelain").count("worktree ")

    def test_exact_blobs_not_working_tree_not_attributes(self):
        write(os.path.join(self.src, "a.txt"), "dirty\n")
        write(os.path.join(self.src, "untracked.txt"), "x\n")
        h0, g0 = tree_hash(self.src), git_dir_hash(self.src)
        co = Checkout(self.src, self.c1.upper())
        try:
            blob = subprocess.run(["git", "-C", self.src, "cat-file", "blob", "%s:a.txt" % self.c1],
                                  stdout=subprocess.PIPE).stdout
            with open(os.path.join(co.path, "a.txt"), "rb") as f:
                got = f.read()
            self.assertEqual(got, blob)  # the stored bytes; .gitattributes eol=crlf is not applied (git add stored LF)
            self.assertNotIn(b"\r", got)
            with open(os.path.join(co.path, "ignored.txt")) as f:  # export-ignore does not drop it
                self.assertEqual(f.read().strip(), "must still be exported")
            self.assertTrue(os.path.isfile(os.path.join(co.path, "sub", "b.txt")))
            self.assertFalse(os.path.exists(os.path.join(co.path, "untracked.txt")))
            self.assertFalse(os.path.lexists(os.path.join(co.path, ".git")))
            self.assertFalse(os.path.lexists(os.path.join(os.path.dirname(co.path), ".git")))
            self.assertEqual(self.worktrees(), 1)  # nothing is registered in the source repository
        finally:
            rec = co.finish()
        self.assertEqual((rec["cleanup"], rec["mode"], rec["head_sha"]), ("REMOVED", "TREE_EXPORT_FROM_SHA", self.c1))
        self.assertEqual(rec["files_written"], 4)  # .gitattributes, a.txt, ignored.txt, sub/b.txt
        self.assertTrue(rec["blobs_verified"] and not rec["has_git_entry"])
        self.assertEqual(rec["source_head_before"], rec["source_head_after"])
        self.assertFalse(os.path.exists(co.path))
        self.assertEqual(tree_hash(self.src), h0)
        self.assertEqual(git_dir_hash(self.src), g0)  # the source .git is not written
        self.assertEqual(co.finish(), rec)  # idempotent

    def test_checkout_is_not_inside_a_repository(self):
        co = Checkout(self.src, self.c1)
        try:
            p = subprocess.run(["git", "-C", co.path, "rev-parse", "--git-dir"], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
            self.assertNotEqual(p.returncode, 0)  # no way back to the source repository from the checkout
        finally:
            co.finish()

    def test_names_and_abbreviations_are_refused(self):
        for bad in ("HEAD", "v1", "side", self.c1[:7], self.c1[:39], self.c1 + "0", "z" * 40, "", None, self.c1 + "^"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                Checkout(self.src, bad)

    def test_unknown_and_non_commit_objects_are_refused(self):
        blob = git(self.src, "rev-parse", "%s:a.txt" % self.c1)
        tree = git(self.src, "rev-parse", "%s^{tree}" % self.c1)
        for bad in ("0" * 40, blob, tree):
            with self.assertRaises(ValueError, msg=bad):
                Checkout(self.src, bad)
        self.assertEqual([d for d in os.listdir(tempfile.gettempdir()) if d.startswith("reprogate-checkout-")
                          and os.path.exists(os.path.join(tempfile.gettempdir(), d, "repo"))], [])

    def test_source_that_is_not_a_repository_is_refused(self):
        with self.assertRaises(ValueError):
            Checkout(self.tmp, self.c1)
        with self.assertRaises(ValueError):
            Checkout(os.path.join(self.tmp, "nope"), self.c1)

    def test_path_validator(self):
        for ok in ("a.txt", "sub/b.txt", "a/b/c/d.py", ".gitattributes", ".github/x.yml"):
            self.assertEqual(safe_relpath(ok), ok.split("/"))
        for bad in ("/etc/passwd", "\\x", "C:/x", "c:\\x", "../x", "a/../x", "a//b", "a/./b", "", ".git/config",
                    "a/.git/hooks/x", ".GIT/x", ".git./x", "sub\\x", "a\0b", None):
            with self.assertRaises(ValueError, msg=repr(bad)):
                safe_relpath(bad)

    def test_tampered_blob_is_detected(self):
        # damage the loose object of a.txt: the id check (or git itself) must stop the export, leaving nothing behind
        oid = git(self.src, "rev-parse", "%s:a.txt" % self.c1)
        path = os.path.join(self.src, ".git", "objects", oid[:2], oid[2:])
        os.chmod(path, 0o666)
        with open(path, "wb") as f:
            f.write(b"not a zlib stream")
        with self.assertRaises(ValueError):
            Checkout(self.src, self.c1)
        self.assertEqual([d for d in os.listdir(tempfile.gettempdir()) if d.startswith("reprogate-checkout-")
                          and os.path.exists(os.path.join(tempfile.gettempdir(), d, "repo"))], [])

    @unittest.skipIf(os.name == "nt", "exec bit and symlinks need POSIX")
    def test_exec_bit_and_symlink_on_posix(self):
        script = os.path.join(self.src, "run.sh")
        write(script, "#!/bin/sh\n")
        os.chmod(script, 0o755)
        os.symlink("run.sh", os.path.join(self.src, "link"))
        git(self.src, "add", "-A")
        git(self.src, "update-index", "--chmod=+x", "run.sh")
        git(self.src, "commit", "-q", "-m", "x")
        sha = git(self.src, "rev-parse", "HEAD")
        co = Checkout(self.src, sha)
        try:
            self.assertTrue(os.access(os.path.join(co.path, "run.sh"), os.X_OK))
            self.assertEqual(os.readlink(os.path.join(co.path, "link")), "run.sh")
            self.assertEqual(co.finish()["symlinks_created"], 1)
        finally:
            co.finish()


class CheckoutEvaluateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rg-co-ev-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.src = H.make_repo(os.path.join(self.tmp, "src"))
        git(self.src, "init", "-q")
        git(self.src, "add", "-A")
        git(self.src, "commit", "-q", "-m", "buggy")
        self.buggy = git(self.src, "rev-parse", "HEAD")
        H.make_repo(os.path.join(self.tmp, "fixed"), fixed=True)
        shutil.copyfile(os.path.join(self.tmp, "fixed", "minilib", "box.py"),
                        os.path.join(self.src, "minilib", "box.py"))
        git(self.src, "commit", "-q", "-a", "-m", "fix")
        self.fixed = git(self.src, "rev-parse", "HEAD")
        self.claim = H.verified_claim()

    def one_worktree(self):
        return git(self.src, "worktree", "list", "--porcelain").count("worktree ") == 1

    def test_evaluate_records_checkout_and_cleans_up(self):
        repro = H.write_repro(self.tmp, "r.py", H.GOOD_REPRO)
        out = os.path.join(self.tmp, "ev")
        g0 = git_dir_hash(self.src)
        o = evaluate(self.src, H.PYTHON, self.claim, repro, out, checkout_sha=self.buggy, **FAST)  # source is at the fix
        self.assertEqual(o["outcome"], C.SYMPTOM_REPRODUCED)
        with open(os.path.join(out, "checkout.json")) as f:
            rec = json.load(f)
        self.assertEqual((rec["requested_sha"], rec["cleanup"]), (self.buggy, "REMOVED"))
        with open(os.path.join(out, "environment.json")) as f:
            self.assertEqual(json.load(f)["git"]["commit"], self.buggy)
        self.assertEqual(o["repository"]["commit"], self.buggy)
        self.assertTrue(self.one_worktree())
        self.assertEqual(git_dir_hash(self.src), g0)

    def test_tracked_file_edited_by_reproducer_is_still_detected_and_source_untouched(self):
        src = ("import os\nfrom minilib import Box\n"
               "p = os.path.join(os.path.dirname(__import__('minilib').__file__), 'box.py')\n"
               "fd = os.open(p, os.O_WRONLY | os.O_APPEND)\nos.write(fd, b'# x')\nos.close(fd)\nBox(2)['a'] = 1\n")
        repro = H.write_repro(self.tmp, "w.py", src)
        h0, g0 = tree_hash(self.src), git_dir_hash(self.src)
        o = evaluate(self.src, H.PYTHON, self.claim, repro, os.path.join(self.tmp, "ev2"), checkout_sha=self.buggy,
                     gate=False, **FAST)
        self.assertEqual((o["outcome"], o["outcome_reason"]), (C.INCONCLUSIVE, C.REPOSITORY_MODIFIED))
        self.assertEqual((tree_hash(self.src), git_dir_hash(self.src)), (h0, g0))

    def test_f050_attacks_find_nothing_to_write_to(self):
        # d2/d3/d4 of F-050 reached the source .git through the worktree's .git pointer; there is no pointer any more
        attack = ("import os\nfrom minilib import Box\n"
                  "d = os.getcwd()\nfound = []\n"
                  "while True:\n"
                  "    if os.path.lexists(os.path.join(d, '.git')):\n        found.append(d)\n"
                  "    up = os.path.dirname(d)\n"
                  "    if up == d:\n        break\n    d = up\n"
                  "if found:\n    raise SystemExit('found .git at ' + ','.join(found))\n"
                  "Box(2)['a'] = 1\n")
        repro = H.write_repro(self.tmp, "up.py", attack)
        o = evaluate(self.src, H.PYTHON, self.claim, repro, os.path.join(self.tmp, "ev5"), checkout_sha=self.buggy,
                     gate=False, **FAST)
        # the reproducer completes (no SystemExit): no .git exists in the checkout or in its parents up to the temp dir;
        # (a .git above the temp directory would be the machine's own business and fails the test loudly)
        self.assertEqual(o["counts"]["completed"], 3, o["run_status"])

    def test_cleanup_when_the_evaluation_raises(self):
        with self.assertRaises(Exception):
            evaluate(self.src, H.PYTHON, self.claim, os.path.join(self.tmp, "no-such-repro.py"),
                     os.path.join(self.tmp, "ev3"), checkout_sha=self.buggy, **FAST)
        self.assertTrue(self.one_worktree())
        self.assertEqual([d for d in os.listdir(tempfile.gettempdir()) if d.startswith("reprogate-checkout-")
                          and os.path.exists(os.path.join(tempfile.gettempdir(), d, "repo"))], [])

    def test_oracle_with_two_shas(self):
        from reprogate.pipeline import oracle
        repro = H.write_repro(self.tmp, "o.py", H.GOOD_REPRO)
        res = oracle(self.src, self.src, H.PYTHON, self.claim, repro, os.path.join(self.tmp, "ev4"),
                     before_sha=self.buggy, after_sha=self.fixed, **FAST)
        self.assertTrue(res["oracle_pass"])
        self.assertTrue(self.one_worktree())


if __name__ == "__main__":
    unittest.main()
