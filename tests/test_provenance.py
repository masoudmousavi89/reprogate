"""Provenance guard (F-027): empty/short/ambiguous/malformed anchors and the claim hash binding."""
import unittest

from reprogate import provenance
from reprogate.provenance import AMBIGUOUS, EMPTY_OR_TOO_SHORT, EXACT, INFERRED, MALFORMED, REJECTED

BODY = (
    "Copying a Box then adding an item crashes.\r\n\r\n```\r\n"
    ">>> b = box.Box(1)\r\n>>> b['foo'] = 'bar'\r\n>>> c = b.copy()\r\n>>> c['blah'] = 'blargh'\r\n"
    "Traceback (most recent call last):\r\n  File \"minilib/box.py\", line 27, in __setitem__\r\n"
    "    del self._mapping[self._popleft()]\r\nIndexError: pop from an empty deque\r\n```\r\n"
).encode("utf-8")

TYPE = {"field": "exception_type", "text": "IndexError"}
MSG = {"field": "message", "text": "pop from an empty deque"}
FILE = {"field": "location_file", "text": "minilib/box.py"}
FUNC = {"field": "location_function", "text": "__setitem__"}


def check(anchors, body=BODY):
    return provenance.check_claim({"claim": {"kind": "exception"}, "anchors": anchors}, body)


def states(doc):
    return [(a["provenance"], a.get("reject_reason")) for a in doc["anchors"]]


class AnchorGuardTests(unittest.TestCase):
    def test_four_good_anchors_are_exact_and_sufficient(self):
        doc = check([TYPE, MSG, FILE, FUNC])
        self.assertTrue(all(s == (EXACT, None) for s in states(doc)))
        self.assertTrue(doc["provenance_sufficient"])
        self.assertEqual(doc["anchors"][0]["occurrences"], 1)

    def test_empty_anchors_are_rejected_and_not_sufficient(self):
        doc = check([{"field": "exception_type", "text": ""}, {"field": "message", "text": ""}])
        self.assertEqual(states(doc), [(REJECTED, EMPTY_OR_TOO_SHORT)] * 2)
        self.assertFalse(doc["provenance_sufficient"])
        self.assertNotIn("start_byte", doc["anchors"][0])

    def test_one_and_two_character_anchors_are_rejected(self):
        doc = check([{"field": "exception_type", "text": "e"}, {"field": "message", "text": "rr"}])
        self.assertEqual(states(doc), [(REJECTED, EMPTY_OR_TOO_SHORT)] * 2)
        self.assertFalse(doc["provenance_sufficient"])

    def test_whitespace_only_anchor_is_rejected(self):
        doc = check([{"field": "exception_type", "text": "    "}, {"field": "message", "text": "    "}])
        self.assertEqual(states(doc), [(REJECTED, EMPTY_OR_TOO_SHORT)] * 2)
        self.assertFalse(doc["provenance_sufficient"])

    def test_three_characters_is_allowed(self):
        doc = check([{"field": "exception_type", "text": "Err"}, FILE])
        self.assertEqual(states(doc), [(EXACT, None), (EXACT, None)])
        self.assertTrue(doc["provenance_sufficient"])

    def test_repeated_anchor_is_ambiguous_and_reported(self):
        doc = check([TYPE, {"field": "message", "text": "Box"}])
        self.assertEqual(states(doc), [(EXACT, None), (REJECTED, AMBIGUOUS)])
        self.assertEqual(doc["anchors"][1]["occurrences"], 2)
        self.assertTrue(doc["anchors"][1]["found"])
        self.assertFalse(doc["provenance_sufficient"])

    def test_ambiguous_anchor_can_be_compensated_by_an_exact_location_anchor(self):
        doc = check([TYPE, {"field": "message", "text": "Box"}, FILE])
        self.assertTrue(doc["provenance_sufficient"])

    def test_anchor_not_in_the_body_stays_inferred(self):
        doc = check([TYPE, {"field": "message", "text": "not in the issue text"}])
        self.assertEqual(states(doc), [(EXACT, None), (INFERRED, None)])
        self.assertFalse(doc["provenance_sufficient"])

    def test_malformed_anchors_are_rejected_without_crashing(self):
        for bad in ({"field": "message"}, {"field": "message", "text": 123}, {"text": "pop from"},
                    {"field": 5, "text": "pop from"}, "just a string", None):
            doc = check([TYPE, bad])
            self.assertEqual(states(doc)[1], (REJECTED, MALFORMED), repr(bad))
            self.assertFalse(doc["provenance_sufficient"], repr(bad))


class ClaimHashTests(unittest.TestCase):
    def test_hash_depends_on_the_issue_snapshot(self):
        a = check([TYPE], b"IndexError at start " + b"x" * 10)
        b = check([TYPE], b"IndexError at start " + b"y" * 10)
        self.assertEqual(a["anchors"][0]["start_byte"], b["anchors"][0]["start_byte"])
        self.assertNotEqual(a["claim_sha256"], b["claim_sha256"])

    def test_hash_is_stable_for_the_same_input(self):
        self.assertEqual(check([TYPE, MSG])["claim_sha256"], check([TYPE, MSG])["claim_sha256"])

    def test_hash_depends_on_the_reject_reason(self):
        short = check([TYPE, {"field": "message", "text": "rr"}])
        absent = check([TYPE, {"field": "message", "text": "not in the issue text"}])
        self.assertNotEqual(short["claim_sha256"], absent["claim_sha256"])


if __name__ == "__main__":
    unittest.main()
