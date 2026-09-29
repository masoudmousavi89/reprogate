"""F-023: the harness is a supervisor plus a worker; cheap observation forgery must not give SYMPTOM_REPRODUCED."""
import os
import unittest

from reprogate import constants as C
from reprogate.pipeline import evaluate
from tests import helpers as H

FORGED = """import json, os
from minilib import Box
with open('/proc/self/cmdline', 'rb') as f:
    argv = f.read().split(b'\\0')
key = b'--result-file' if b'--result-file' in argv else b'--out'
path = argv[argv.index(key) + 1].decode()
obs = {"harness_version": "0.1-proto", "observation_integrity": "X", "python": {"version": "3", "implementation": "c"},
       "exit_code": 1, "phase": "trigger",
       "exception": {"type": "IndexError", "module": "builtins", "message": "pop from an empty deque",
                     "frames": [{"index": 0, "class": "TARGET", "function": "__setitem__", "lineno": 1, "filename": "x",
                                 "module": "minilib.box", "authentic": True, "rel_path": "minilib/box.py"}],
                     "chain": [], "raised_by_reproducer_statement": False}}
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
os.write(fd, json.dumps(%s).encode())
os.close(fd)
%s
"""


@unittest.skipIf(os.name == "nt", "process-signal attacks are POSIX only")
class ForgeryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = H.tmpdir()
        self.repo = H.make_repo(os.path.join(self.tmp, "buggy"))

    def tearDown(self):
        H.cleanup(self.tmp)

    def run_case(self, name, src):
        repro = H.write_repro(self.tmp, name + ".py", src)
        return evaluate(self.repo, H.PYTHON, H.verified_claim(), repro, os.path.join(self.tmp, "ev-" + name),
                        runs=3, timeout=20, min_completed=3)

    def test_forged_output_file_then_abort_is_not_accepted(self):
        o = self.run_case("f1", FORGED % ("obs", "os.abort()"))
        self.assertNotEqual(o["outcome"], C.SYMPTOM_REPRODUCED)

    def test_forged_output_file_then_kill_whole_group_is_not_accepted(self):
        o = self.run_case("f2", FORGED % ("obs", "os.killpg(os.getpgrp(), 9)"))
        self.assertNotEqual(o["outcome"], C.SYMPTOM_REPRODUCED)

    def test_forged_result_file_then_normal_end_is_not_accepted(self):
        # the real worker cannot create its result file any more (O_EXCL), so the run is invalid
        o = self.run_case("f3", FORGED % ('{"protocol": "rg-obs-1", "obs": obs}', "pass"))
        self.assertNotEqual(o["outcome"], C.SYMPTOM_REPRODUCED)

    def test_protocol_aware_forgery_with_fake_frame_is_not_accepted(self):
        # b02 shape (F-026): valid result message, hidden os._exit; the fake TARGET frame fails the source check
        o = self.run_case("f4", FORGED % ('{"protocol": "rg-obs-1", "obs": obs}', "getattr(os, '_e' + 'xit')(1)"))
        self.assertNotEqual(o["outcome"], C.SYMPTOM_REPRODUCED)

    def test_honest_reproducer_still_reproduces(self):
        o = self.run_case("good", H.GOOD_REPRO)
        self.assertEqual(o["outcome"], C.SYMPTOM_REPRODUCED)


if __name__ == "__main__":
    unittest.main()
