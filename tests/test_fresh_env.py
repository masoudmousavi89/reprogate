"""Fresh environment per run (F-032): --env-template gives every run a new copy of the environment."""
import glob
import json
import os
import shutil
import sys
import tempfile
import unittest
import venv

from reprogate import constants as C
from reprogate.invariants import validate_outcome
from reprogate.pipeline import ENV_FRESH, ENV_SHARED, evaluate
from reprogate.runner import tree_hash
from tests import helpers as H

FAST = dict(runs=3, timeout=30, min_completed=3)


def venv_python(root):
    sub = "Scripts" if os.name == "nt" else "bin"
    return os.path.join(root, sub, "python.exe" if os.name == "nt" else "python")


MARKER_REPRO = """import os, sys
from minilib import Box

fd = os.open(os.path.join(sys.prefix, "marker.txt"), os.O_WRONLY | os.O_CREAT | os.O_APPEND)
os.write(fd, b"x")
os.close(fd)
Box(2)["a"] = 1
print("done")
"""

TEMPLATE_WRITER = """import os
from minilib import Box

fd = os.open(r"%s", os.O_WRONLY | os.O_CREAT | os.O_APPEND)
os.write(fd, b"x")
os.close(fd)
Box(2)["a"] = 1
"""


class FreshEnvTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.mkdtemp(prefix="rg-test-venv-")
        # F-038: symlink on POSIX; a copied interpreter of a shared-library CPython (uv) cannot find libpython
        venv.create(os.path.join(cls.base, "v"), with_pip=False, symlinks=(os.name != "nt"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base, ignore_errors=True)

    def setUp(self):
        self.tmp = H.tmpdir()
        self.repo = H.make_repo(os.path.join(self.tmp, "repo"), fixed=True)
        self.claim = H.verified_claim()

    def tearDown(self):
        H.cleanup(self.tmp)

    def new_venv(self, name):
        dst = os.path.join(self.tmp, name)
        shutil.copytree(os.path.join(self.base, "v"), dst, symlinks=True)
        return dst

    def evaluate(self, src, venv_dir, template=None, name="r", **kw):
        repro = H.write_repro(self.tmp, name + ".py", src)
        return evaluate(self.repo, venv_python(venv_dir), self.claim, repro, os.path.join(self.tmp, "ev-" + name),
                        env_template=template, **dict(FAST, **kw))

    def test_fresh_copy_leaves_the_template_untouched_and_records_the_mode(self):
        tmpl = self.new_venv("tmpl")
        before = tree_hash(tmpl)
        leftovers = set(glob.glob(os.path.join(tempfile.gettempdir(), "reprogate-env-*")))
        o = self.evaluate(MARKER_REPRO, tmpl, template=tmpl)
        self.assertFalse(os.path.exists(os.path.join(tmpl, "marker.txt")))
        self.assertEqual(tree_hash(tmpl), before)
        self.assertEqual(o["environment_mode"], ENV_FRESH)
        self.assertEqual(o["counts"]["completed"], 3)
        self.assertEqual(validate_outcome(o), [])
        with open(os.path.join(self.tmp, "ev-r", "environment.json"), encoding="utf-8") as f:
            iso = json.load(f)["environment_isolation"]
        self.assertEqual(iso["mode"], ENV_FRESH)
        self.assertEqual(iso["template_tree_sha256"], before[0])
        for i in (1, 2, 3):
            with open(os.path.join(self.tmp, "ev-r", "runs", "run-%02d" % i, "run.json"), encoding="utf-8") as f:
                self.assertGreaterEqual(json.load(f)["env_copy_seconds"], 0)
        self.assertEqual(set(glob.glob(os.path.join(tempfile.gettempdir(), "reprogate-env-*"))), leftovers)

    def test_control_without_a_template_the_marker_persists(self):
        shared = self.new_venv("shared")
        o = self.evaluate(MARKER_REPRO, shared)
        self.assertEqual(o["environment_mode"], ENV_SHARED)
        with open(os.path.join(shared, "marker.txt"), "rb") as f:
            self.assertEqual(f.read(), b"xxx")  # one byte per run, all three runs wrote into the same environment

    def test_same_template_gives_the_same_recorded_hash_and_outcome(self):
        tmpl = self.new_venv("tmpl")
        a = self.evaluate(MARKER_REPRO, tmpl, template=tmpl, name="a")
        b = self.evaluate(MARKER_REPRO, tmpl, template=tmpl, name="b")
        self.assertEqual((a["outcome"], a["outcome_reason"], a["counts"]), (b["outcome"], b["outcome_reason"], b["counts"]))
        h = []
        for n in ("a", "b"):
            with open(os.path.join(self.tmp, "ev-" + n, "environment.json"), encoding="utf-8") as f:
                h.append(json.load(f)["environment_isolation"]["template_tree_sha256"])
        self.assertEqual(h[0], h[1])

    def test_reproducer_writing_into_the_template_aborts_before_the_next_run(self):
        tmpl = self.new_venv("tmpl")
        src = TEMPLATE_WRITER % os.path.join(tmpl, "poison.txt").replace("\\", "\\\\")
        with self.assertRaises(ValueError) as cm:
            self.evaluate(src, tmpl, template=tmpl)
        self.assertIn("template changed", str(cm.exception))

    def test_docker_with_a_template_is_refused(self):
        tmpl = self.new_venv("tmpl")
        with self.assertRaises(ValueError):
            self.evaluate(MARKER_REPRO, tmpl, template=tmpl, sandbox={"kind": "docker"})

    def test_python_outside_the_template_is_refused(self):
        tmpl = self.new_venv("tmpl")
        other = self.new_venv("other")
        repro = H.write_repro(self.tmp, "x.py", MARKER_REPRO)
        with self.assertRaises(ValueError):
            evaluate(self.repo, venv_python(other), self.claim, repro, os.path.join(self.tmp, "ev-x"),
                     env_template=tmpl, **FAST)

    def test_missing_template_directory_is_refused(self):
        with self.assertRaises(ValueError):
            evaluate(self.repo, sys.executable, self.claim, H.write_repro(self.tmp, "y.py", MARKER_REPRO),
                     os.path.join(self.tmp, "ev-y"), env_template=os.path.join(self.tmp, "nope"), **FAST)


if __name__ == "__main__":
    unittest.main()
