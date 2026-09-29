"""Matcher rules (F-033, req_009): innermost causal target frame, short messages, origin/causal evidence fields."""
import importlib.util
import os
import unittest

from reprogate.matcher import MIN_MESSAGE_CHARS, classify_run
from reprogate.pipeline import _anchor_states

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_cases():
    path = os.path.join(ROOT, "labs", "matcher-rules", "cases.py")
    spec = importlib.util.spec_from_file_location("matcher_rule_cases", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CASES = _load_cases()

# id prefix -> (symptom_match, reasons that must be present, reasons that must be absent, origin, causal)
EXPECTED = {
    "m01": (True, set(), {"LOCATION_MISMATCH"}, "TARGET#1:__setitem__", "TARGET#1:__setitem__"),
    "m02": (True, {"LOCATION_MISMATCH"}, set(), "TARGET#2:_helper", "TARGET#2:_helper"),
    "m03": (False, {"LOCATION_MISMATCH"}, set(), "TARGET#2:_helper", "TARGET#2:_helper"),
    "m04": (True, set(), {"LOCATION_MISMATCH"}, "TARGET#1:__setitem__", "TARGET#1:__setitem__"),
    "m05": (True, {"MESSAGE_TOO_SHORT_IGNORED"}, {"MESSAGE_MISMATCH"}, "TARGET#1:__setitem__", "TARGET#1:__setitem__"),
    "m06": (False, {"MESSAGE_TOO_SHORT_IGNORED"}, set(), "TARGET#1:__setitem__", "TARGET#1:__setitem__"),
    "m07": (True, set(), {"MESSAGE_TOO_SHORT_IGNORED"}, "TARGET#1:__setitem__", "TARGET#1:__setitem__"),
    "m08": (True, set(), set(), "STDLIB#2:popleft", "TARGET#1:__setitem__"),
    "m09": (False, {"LOCATION_MISMATCH"}, set(), "STDLIB#3:popleft", "TARGET#2:_helper"),
    "m10": (False, {"FORGED_TARGET_FRAME"}, set(), "FORGED_TARGET#2:__setitem__", "TARGET#1:__setitem__"),
    "m11": (False, {"REPRODUCER_FRAME_AFTER_TARGET"}, set(), "REPRODUCER#2:cb", "TARGET#1:__setitem__"),
    "m12": (False, set(), set(), "TARGET#1:__setitem__", "TARGET#1:__setitem__"),
    "m13": (True, {"ORIGIN_FROM_INTERPRETER_CONVERSION"}, set(), "STDLIB#1:next_", "TARGET#1:gen"),
    "m14": (False, {"NO_EXCEPTION_OBSERVED"}, set(), None, None),
}


class MatcherRuleTests(unittest.TestCase):
    def test_every_case_matches_its_expectation(self):
        self.assertEqual(len(CASES.CASES), len(EXPECTED))
        for cid, claim, ob in CASES.CASES:
            match, present, absent, origin, causal = EXPECTED[cid[:3]]
            v = classify_run(ob, claim)
            self.assertEqual(v["symptom_match"], match, cid)
            self.assertTrue(present <= set(v["reasons"]), "%s: %s" % (cid, v["reasons"]))
            self.assertFalse(absent & set(v["reasons"]), "%s: %s" % (cid, v["reasons"]))
            self.assertEqual(CASES.short(v["exception_origin"]) if origin else None, origin, cid)
            self.assertEqual(CASES.short(v["target_causal_frame"]) if causal else None, causal, cid)
            if not origin:
                self.assertIsNone(v["exception_origin"])
            if not causal:
                self.assertIsNone(v["target_causal_frame"])

    def test_conversion_cause_frame_is_marked(self):
        cid, claim, ob = [c for c in CASES.CASES if c[0].startswith("m13")][0]
        self.assertEqual(classify_run(ob, claim)["target_causal_frame"]["via"], "interpreter_conversion_cause")

    def test_minimum_message_length_constant(self):
        self.assertEqual(MIN_MESSAGE_CHARS, 3)

    def test_whitespace_only_message_is_ignored_like_no_message(self):
        claim = {"kind": "exception", "exception_type": "ValueError", "message": "   ", "location": CASES.LOC}
        v = classify_run(CASES.obs("ValueError", "x", [CASES.REPRO, CASES.INNER_SAME]), claim)
        self.assertTrue(v["symptom_match"])
        self.assertIn("MESSAGE_TOO_SHORT_IGNORED", v["reasons"])

    def test_empty_message_adds_no_reason(self):
        claim = {"kind": "exception", "exception_type": "ValueError", "message": "", "location": CASES.LOC}
        v = classify_run(CASES.obs("ValueError", "x", [CASES.REPRO, CASES.INNER_SAME]), claim)
        self.assertTrue(v["symptom_match"])
        self.assertNotIn("MESSAGE_TOO_SHORT_IGNORED", v["reasons"])

    def test_evidence_fields_do_not_carry_absolute_paths(self):
        cid, claim, ob = CASES.CASES[0]
        v = classify_run(ob, claim)
        for f in (v["exception_origin"], v["target_causal_frame"]):
            self.assertEqual(set(f), {"index", "class", "function", "rel_path"})


class AnchorStateTests(unittest.TestCase):
    def test_states_are_evidence_only(self):
        doc = {"anchors": [
            {"field": "exception_type", "provenance": "EXACT_QUOTE"},
            {"field": "message", "provenance": "REJECTED", "reject_reason": "AMBIGUOUS"},
            {"field": "location_file", "provenance": "INFERRED"},
            {"field": "location_function"},
            "not a dict", {"text": "no field"}]}
        verified, not_verified = _anchor_states(doc)
        self.assertEqual(verified, ["exception_type"])
        self.assertEqual(not_verified, {"location_file": "INFERRED", "location_function": "UNVERIFIED",
                                        "message": "AMBIGUOUS"})

    def test_missing_anchors(self):
        self.assertEqual(_anchor_states({}), ([], {}))


if __name__ == "__main__":
    unittest.main()
