"""F-011 (raise inside callbacks) and F-012 (PEP 479 origin via exception cause). Synthetic library."""
import os
import unittest

from reprogate import constants as C
from reprogate.gate import gate_source
from reprogate.pipeline import evaluate
from tests import helpers as H

GENLIB_BUGGY = '''
def iterate(func, start):
    while True:
        yield start
        start = func(start)
'''
GENLIB_FIXED = '''
def iterate(func, start):
    while True:
        yield start
        try:
            start = func(start)
        except StopIteration:
            break
'''
CLAIM = {
    "schema_version": "0.1-proto",
    "issue": {"number": 2},
    "claim": {"kind": "exception", "exception_type": "RuntimeError", "message": "generator raised StopIteration",
              "location": {"file": "genlib/core.py", "function": "iterate"}},
    "anchors": [{"field": "exception_type", "text": "RuntimeError"}],
}
GOOD = """from itertools import islice
from genlib import iterate


def func(n):
    if n > 100:
        raise StopIteration
    return n * 2


print(list(islice(iterate(func, 1), 10)))
"""


def gate(src):
    r = gate_source(src.encode("utf-8"))
    return r["status"], {f["code"] for f in r["findings"]}


class GateScopeTests(unittest.TestCase):
    def test_raise_inside_function_is_allowed(self):
        self.assertEqual(gate("def f():\n    if 1:\n        raise StopIteration\n"), ("VALID", set()))

    def test_raise_outside_function_or_in_handler_is_rejected(self):
        for src in ("raise IndexError('x')\n",
                    "class C:\n    raise IndexError('x')\n",
                    "try:\n    pass\nexcept Exception:\n    raise IndexError('x')\n",
                    "def f():\n    try:\n        pass\n    except Exception:\n        raise IndexError('x')\n"):
            st, c = gate(src)
            self.assertEqual(st, "REJECTED", src)
            self.assertIn("DIRECT_RAISE", c)


class ConversionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = H.tmpdir()
        self.buggy = self._repo("buggy", GENLIB_BUGGY)
        self.fixed = self._repo("fixed", GENLIB_FIXED)

    def tearDown(self):
        H.cleanup(self.tmp)

    def _repo(self, name, code):
        pkg = os.path.join(self.tmp, name, "genlib")
        os.makedirs(pkg)
        with open(os.path.join(pkg, "core.py"), "w") as f:
            f.write(code)
        with open(os.path.join(pkg, "__init__.py"), "w") as f:
            f.write("from .core import iterate\n")
        return os.path.join(self.tmp, name)

    def run_case(self, name, src, repo=None, gate=True):
        repro = H.write_repro(self.tmp, name + ".py", src)
        return evaluate(repo or self.buggy, H.PYTHON, CLAIM, repro, os.path.join(self.tmp, "ev-" + name),
                        gate=gate, runs=3, timeout=20, min_completed=3, allow_unverified_provenance=True)

    def test_callback_raising_stopiteration_reproduces_on_buggy(self):
        o = self.run_case("good", GOOD)
        self.assertEqual((o["outcome"], o["outcome_reason"]), (C.SYMPTOM_REPRODUCED, C.NONE))

    def test_same_reproducer_completes_cleanly_on_fixed(self):
        o = self.run_case("good_fixed", GOOD, repo=self.fixed)
        self.assertEqual(o["outcome"], C.NO_MATCHING_REPRODUCTION_FOUND)
        self.assertEqual(o["counts"]["clean_completion_runs"], 3)

    def test_runtimeerror_raised_by_reproducer_function_is_not_accepted(self):
        src = ("import genlib\n\n\ndef g():\n    raise RuntimeError('generator raised StopIteration')\n\n\ng()\n")
        self.assertEqual(self.run_case("f_fn", src)["outcome"], C.NO_MATCHING_REPRODUCTION_FOUND)

    def test_fake_cause_without_target_frame_is_not_accepted(self):
        src = ("import genlib\n\n\ndef g():\n    raise RuntimeError('generator raised StopIteration') from StopIteration()\n\n\ng()\n")
        self.assertEqual(self.run_case("f_cause", src)["outcome"], C.NO_MATCHING_REPRODUCTION_FOUND)

    def test_own_generator_conversion_without_target_is_not_accepted(self):
        src = ("import genlib\n\n\ndef gen():\n    yield 1\n    next(iter(()))\n\n\nlist(gen())\n")
        self.assertEqual(self.run_case("f_own", src)["outcome"], C.NO_MATCHING_REPRODUCTION_FOUND)

    def test_callback_raising_claimed_runtimeerror_is_not_accepted(self):
        src = ("from genlib import iterate\n\n\ndef func(n):\n    raise RuntimeError('generator raised StopIteration')\n\n\n"
               "list(iterate(func, 1))\n")
        self.assertEqual(self.run_case("f_cb", src)["outcome"], C.NO_MATCHING_REPRODUCTION_FOUND)


if __name__ == "__main__":
    unittest.main()
