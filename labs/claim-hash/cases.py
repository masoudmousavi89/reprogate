"""Claim hash cases (F-042). Pure calls to provenance_state on frozen claims; nothing is executed.

Usage (repo root): py -3.8 labs/claim-hash/cases.py
Prints one line per case: case | state (VERIFIED, INSUFFICIENT, UNVERIFIED_ALLOWED) or ValueError.
"""
import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from reprogate.provenance import check_claim, claim_hash, provenance_state  # noqa: E402

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
CLAIM = {"kind": "exception", "exception_type": "IndexError", "message": "pop from an empty deque",
         "location": {"file": "minilib/box.py", "function": "__setitem__"}}


def frozen(anchors):
    return check_claim({"claim": copy.deepcopy(CLAIM), "anchors": anchors}, BODY)


def state(doc, allow=False):
    try:
        return provenance_state(doc, allow)
    except ValueError:
        return "ValueError"


def edited(fn, anchors=(TYPE, MSG, FILE, FUNC)):
    doc = frozen(list(anchors))
    fn(doc)
    return doc


def main():
    rows = []
    rows.append(("h00_control_unmodified", state(frozen([TYPE, MSG, FILE, FUNC]))))
    rows.append(("h01_claim_message_edited_after_freezing",
                 state(edited(lambda d: d["claim"].update(message="something else")))))
    rows.append(("h02_anchor_text_edited",
                 state(edited(lambda d: d["anchors"][1].update(text="another text")))))
    # h03: the message anchor is not in the body (INFERRED); flip it to EXACT by hand without recomputing anything
    rows.append(("h03_inferred_anchor_flipped_to_exact_by_hand",
                 state(edited(lambda d: d["anchors"][1].update(provenance="EXACT_QUOTE", found=True),
                              anchors=(TYPE, {"field": "message", "text": "not in the issue text"})))))
    rows.append(("h04_issue_body_sha_edited",
                 state(edited(lambda d: d["issue"].update(body_sha256="0" * 64)))))
    # h05: only the exception type is anchored (insufficient); the flag is set to True by hand
    rows.append(("h05_sufficient_flag_set_by_hand",
                 state(edited(lambda d: d.update(provenance_sufficient=True), anchors=(TYPE,)))))
    rows.append(("h06_claim_sha256_removed", state(edited(lambda d: d.pop("claim_sha256")))))

    def recomputed(d):
        d["claim"]["message"] = "something else"
        d["claim_sha256"] = claim_hash(d)
    rows.append(("h07_claim_edited_and_hash_recomputed", state(edited(recomputed))))
    rows.append(("h08_unverified_not_allowed",
                 state({"claim": copy.deepcopy(CLAIM), "anchors": [TYPE]}, allow=False)))
    rows.append(("h09_unverified_allowed",
                 state({"claim": copy.deepcopy(CLAIM), "anchors": [TYPE]}, allow=True)))
    rows.append(("h10_note_field_outside_the_hash_edited", state(edited(lambda d: d.update(note="x")))))
    rows.append(("h11_claim_sha256_wrong_type", state(edited(lambda d: d.update(claim_sha256=123)))))
    for name, st in rows:
        print("%-48s %s" % (name, st))


if __name__ == "__main__":
    main()
