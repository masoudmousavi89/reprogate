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



class FrozenClaimCheckTests(unittest.TestCase):
    """F-042: a frozen claim edited afterwards is rejected; sufficiency is recomputed from the anchors."""

    @staticmethod
    def frozen(anchors=(TYPE, MSG, FILE, FUNC)):
        claim = {"kind": "exception", "exception_type": "IndexError", "message": "pop from an empty deque"}
        return provenance.check_claim({"claim": claim, "anchors": list(anchors)}, BODY)

    def state(self, doc):
        return provenance.provenance_state(doc, False)

    def test_unmodified_frozen_claim_is_verified(self):
        self.assertEqual(self.state(self.frozen()), "VERIFIED")

    def test_edits_after_freezing_are_rejected(self):
        edits = {
            "claim message": lambda d: d["claim"].update(message="something else"),
            "anchor text": lambda d: d["anchors"][1].update(text="another text"),
            "issue body hash": lambda d: d["issue"].update(body_sha256="0" * 64),
            "hash removed": lambda d: d.pop("claim_sha256"),
            "hash of the wrong type": lambda d: d.update(claim_sha256=123),
        }
        for name, edit in edits.items():
            doc = self.frozen()
            edit(doc)
            with self.assertRaises(ValueError, msg=name) as cm:
                self.state(doc)
            self.assertIn("changed after freezing", str(cm.exception), name)

    def test_inferred_anchor_flipped_to_exact_by_hand_is_rejected(self):
        doc = self.frozen([TYPE, {"field": "message", "text": "not in the issue text"}])
        doc["anchors"][1].update(provenance=EXACT, found=True)
        with self.assertRaises(ValueError):
            self.state(doc)

    def test_sufficiency_is_recomputed_not_read_from_the_flag(self):
        doc = self.frozen([TYPE])
        self.assertFalse(doc["provenance_sufficient"])
        doc["provenance_sufficient"] = True
        self.assertEqual(self.state(doc), "INSUFFICIENT")

    def test_fields_outside_the_hash_stay_editable(self):
        doc = self.frozen()
        doc["note"] = "free text"
        self.assertEqual(self.state(doc), "VERIFIED")

    def test_known_limit_edit_plus_recomputed_hash_passes(self):
        doc = self.frozen()
        doc["claim"]["message"] = "something else"
        doc["claim_sha256"] = provenance.claim_hash(doc)
        self.assertEqual(self.state(doc), "VERIFIED")

    def test_unverified_documents_keep_their_behaviour(self):
        doc = {"claim": {"kind": "exception"}, "anchors": [TYPE]}
        with self.assertRaises(ValueError):
            provenance.provenance_state(doc, False)
        self.assertEqual(provenance.provenance_state(doc, True), "UNVERIFIED_ALLOWED")


if __name__ == "__main__":
    unittest.main()
