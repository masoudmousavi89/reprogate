"""Fresh checkout of an exact SHA (req_005, labs/checkout-sha/PREDICTIONS.md)."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

from reprogate import constants as C
from reprogate.checkout import Checkout
from reprogate.pipeline import evaluate
from reprogate.runner import tree_hash
from tests import helpers as H

FAST = dict(runs=3, timeout=30, min_completed=3)


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.autocrlf=false"]
                       + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.stdout.decode().strip()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        f.write(text)


class CheckoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rg-co-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.src = os.path.join(self.tmp, "src")
        os.makedirs(self.src)
        git(self.src, "init", "-q")
        write(os.path.join(self.src, "a.txt"), "one\n")
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

    def test_exact_commit_not_working_tree(self):
        write(os.path.join(self.src, "a.txt"), "dirty\n")
        write(os.path.join(self.src, "untracked.txt"), "x\n")
        h0 = tree_hash(self.src)
        co = Checkout(self.src, self.c1.upper())
        try:
            self.assertEqual(git(co.path, "rev-parse", "HEAD"), self.c1)
            self.assertEqual(git(co.path, "status", "--porcelain"), "")
            with open(os.path.join(co.path, "a.txt")) as f:
                self.assertEqual(f.read().strip(), "one")
            self.assertFalse(os.path.exists(os.path.join(co.path, "untracked.txt")))
            self.assertEqual(self.worktrees(), 2)
        finally:
            rec = co.finish()
        self.assertEqual(rec["cleanup"], "REMOVED")
        self.assertEqual(rec["head_sha"], self.c1)
        self.assertEqual(rec["source_head_before"], rec["source_head_after"])
        self.assertFalse(os.path.exists(co.path))
        self.assertEqual(self.worktrees(), 1)
        self.assertEqual(tree_hash(self.src), h0)  # the source working tree is untouched
        self.assertEqual(co.finish(), rec)  # idempotent

    def test_names_and_abbreviations_are_refused(self):
        for bad in ("HEAD", "v1", "side", self.c1[:7], self.c1[:39], self.c1 + "0", "z" * 40, "", None, self.c1 + "^"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                Checkout(self.src, bad)
        self.assertEqual(self.worktrees(), 1)

    def test_unknown_and_non_commit_objects_are_refused(self):
        blob = git(self.src, "rev-parse", "%s:a.txt" % self.c1)
        tree = git(self.src, "rev-parse", "%s^{tree}" % self.c1)
        for bad in ("0" * 40, blob, tree):
            with self.assertRaises(ValueError, msg=bad):
                Checkout(self.src, bad)
        self.assertEqual(self.worktrees(), 1)
        self.assertEqual([d for d in os.listdir(tempfile.gettempdir()) if d.startswith("reprogate-checkout-")
                          and os.path.exists(os.path.join(tempfile.gettempdir(), d, "repo"))], [])

    def test_source_that_is_not_a_repository_is_refused(self):
        with self.assertRaises(ValueError):
            Checkout(self.tmp, self.c1)
        with self.assertRaises(ValueError):
            Checkout(os.path.join(self.tmp, "nope"), self.c1)


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
        o = evaluate(self.src, H.PYTHON, self.claim, repro, out, checkout_sha=self.buggy, **FAST)  # source is at the fix
        self.assertEqual(o["outcome"], C.SYMPTOM_REPRODUCED)
        with open(os.path.join(out, "checkout.json")) as f:
            rec = json.load(f)
        self.assertEqual((rec["requested_sha"], rec["cleanup"]), (self.buggy, "REMOVED"))
        with open(os.path.join(out, "environment.json")) as f:
            self.assertEqual(json.load(f)["git"]["commit"], self.buggy)
        self.assertEqual(o["repository"]["commit"], self.buggy)
        self.assertTrue(self.one_worktree())

    def test_tracked_file_edited_by_reproducer_is_still_detected_and_source_untouched(self):
        src = ("import os\nfrom minilib import Box\n"
               "p = os.path.join(os.path.dirname(__import__('minilib').__file__), 'box.py')\n"
               "fd = os.open(p, os.O_WRONLY | os.O_APPEND)\nos.write(fd, b'# x')\nos.close(fd)\nBox(2)['a'] = 1\n")
        repro = H.write_repro(self.tmp, "w.py", src)
        h0 = tree_hash(self.src)
        o = evaluate(self.src, H.PYTHON, self.claim, repro, os.path.join(self.tmp, "ev2"), checkout_sha=self.buggy,
                     gate=False, **FAST)
        self.assertEqual((o["outcome"], o["outcome_reason"]), (C.INCONCLUSIVE, C.REPOSITORY_MODIFIED))
        self.assertEqual(tree_hash(self.src), h0)
        self.assertTrue(self.one_worktree())

    def test_cleanup_when_the_evaluation_raises(self):
        with self.assertRaises(Exception):
            evaluate(self.src, H.PYTHON, self.claim, os.path.join(self.tmp, "no-such-repro.py"),
                     os.path.join(self.tmp, "ev3"), checkout_sha=self.buggy, **FAST)
        self.assertTrue(self.one_worktree())

    def test_oracle_with_two_shas(self):
        from reprogate.pipeline import oracle
        repro = H.write_repro(self.tmp, "o.py", H.GOOD_REPRO)
        res = oracle(self.src, self.src, H.PYTHON, self.claim, repro, os.path.join(self.tmp, "ev4"),
                     before_sha=self.buggy, after_sha=self.fixed, **FAST)
        self.assertTrue(res["oracle_pass"])
        self.assertTrue(self.one_worktree())

    def test_line_endings_are_the_bytes_of_the_commit(self):
        sha = self.buggy
        co = Checkout(self.src, sha)
        try:
            with open(os.path.join(co.path, "minilib", "box.py"), "rb") as f:
                got = f.read()
        finally:
            co.finish()
        blob = subprocess.run(["git", "-C", self.src, "show", sha + ":minilib/box.py"], stdout=subprocess.PIPE).stdout
        self.assertEqual(got, blob)


if __name__ == "__main__":
    unittest.main()
