"""F-026: the supervisor checks the worker's TARGET frames against the real source on disk."""
import os
import unittest

from reprogate import harness
from reprogate import matcher
from tests import helpers as H


class FramePlausibilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = H.tmpdir()
        self.repo = H.make_repo(os.path.join(self.tmp, "buggy"))
        self.box = os.path.join(self.repo, "minilib", "box.py")
        with open(self.box) as f:
            lines = f.read().split("\n")
        self.line = {text.strip(): i + 1 for i, text in enumerate(lines) if text.strip()}
        self.ctx = {"repo": harness._rp(self.repo), "repro": harness._rp(os.path.join(self.tmp, "r.py")),
                    "harness": harness._rp(harness.__file__), "stdlib": harness._stdlib_roots()}

    def tearDown(self):
        H.cleanup(self.tmp)

    def frame(self, **kw):
        fr = {"index": 0, "class": "TARGET", "filename": self.box, "function": "__setitem__",
              "lineno": self.line["del self._mapping[self._popleft()]"], "module": "minilib.box",
              "authentic": True, "rel_path": "minilib/box.py"}
        fr.update(kw)
        return fr

    def recheck(self, *frames):
        obs = {"exit_code": 1, "exception": {"type": "IndexError", "message": "pop from an empty deque",
                                             "frames": list(frames), "chain": []}}
        err = harness._recheck(obs, self.ctx, os.path.realpath(self.repo))
        return err, obs

    def only_frame(self, fr):
        err, obs = self.recheck(fr)
        self.assertIsNone(err)
        return obs["exception"]["frames"][0]

    def test_honest_frame_stays_target_and_matches(self):
        err, obs = self.recheck(self.frame())
        self.assertIsNone(err)
        self.assertEqual(obs["exception"]["frames"][0]["class"], "TARGET")
        self.assertTrue(matcher.classify_run(obs, H.CLAIM["claim"])["symptom_match"])

    def test_b02_shape_fake_file_is_forged(self):
        fr = self.only_frame(self.frame(filename="x", lineno=1))
        self.assertEqual((fr["class"], fr["plausibility_note"]), ("FORGED_TARGET", "not_a_target_file"))

    def test_real_file_line_outside_function_is_forged(self):
        fr = self.only_frame(self.frame(lineno=self.line["class Box(object):"]))
        self.assertEqual((fr["class"], fr["plausibility_note"]), ("FORGED_TARGET", "line_outside_function"))

    def test_unknown_function_is_forged(self):
        fr = self.only_frame(self.frame(function="pop"))
        self.assertEqual((fr["class"], fr["plausibility_note"]), ("FORGED_TARGET", "function_not_in_source"))

    def test_rel_path_mismatch_is_forged(self):
        fr = self.only_frame(self.frame(rel_path="minilib/other.py"))
        self.assertEqual((fr["class"], fr["plausibility_note"]), ("FORGED_TARGET", "rel_path_mismatch"))

    def test_worker_negative_is_kept(self):
        fr = self.only_frame(self.frame(authentic=False))
        self.assertEqual(fr["class"], "FORGED_TARGET")

    def test_def_header_line_is_plausible(self):
        fr = self.only_frame(self.frame(lineno=self.line["def __setitem__(self, key, value):"]))
        self.assertEqual(fr["class"], "TARGET")

    def test_reproducer_frame_cannot_claim_target(self):
        repro = os.path.join(self.tmp, "r.py")
        fr = self.only_frame(self.frame(filename=repro, rel_path=None))
        self.assertEqual(fr["class"], "FORGED_TARGET")

    def test_malformed_frame_rejects_observation(self):
        err, _ = self.recheck(self.frame(lineno="12"))
        self.assertEqual(err, "malformed frame record")

    def test_plausible_forgery_is_not_detected(self):
        # b05 shape: known limit. A frame with the real file, function and line passes; the check is no boundary.
        fr = self.only_frame(self.frame(lineno=self.line["self._append(key)"]))
        self.assertEqual(fr["class"], "TARGET")


if __name__ == "__main__":
    unittest.main()
