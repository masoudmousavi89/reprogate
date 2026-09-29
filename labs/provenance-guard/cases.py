"""Provenance guard cases (F-027). Pure function calls on check_claim; no reproducer is executed.

Usage (repo root): py -3.8 labs/provenance-guard/cases.py
Prints one line per case: case | provenance_sufficient | per-anchor "provenance[/reject_reason]".
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from reprogate.provenance import check_claim  # noqa: E402

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


def claim(anchors):
    return {"claim": {"kind": "exception"}, "anchors": anchors}


CASES = [
    ("c00_control_four_good_anchors", [TYPE, MSG, FILE, FUNC]),
    ("c01_empty_anchors", [{"field": "exception_type", "text": ""}, {"field": "message", "text": ""}]),
    ("c02_one_and_two_char_anchors", [{"field": "exception_type", "text": "e"}, {"field": "message", "text": "rr"}]),
    ("c03_whitespace_only_anchors", [{"field": "exception_type", "text": "    "}, {"field": "message", "text": "    "}]),
    ("c04_ambiguous_message_only_type_exact", [TYPE, {"field": "message", "text": "Box"}]),
    ("c05_missing_text_key", [TYPE, {"field": "message"}]),
    ("c06_non_string_text", [TYPE, {"field": "message", "text": 123}]),
    ("c07_boundary_three_chars_unique", [{"field": "exception_type", "text": "Err"}, FILE]),
]


def show(name, doc):
    parts = []
    for a in doc["anchors"]:
        p = a.get("provenance")
        r = a.get("reject_reason")
        parts.append("%s=%s%s" % (a.get("field"), p, ("/" + r) if r else ""))
    print("%-40s sufficient=%-5s %s" % (name, doc["provenance_sufficient"], "; ".join(parts)))


def run_one(name, anchors):
    try:
        show(name, check_claim(claim(anchors), BODY))
    except Exception as e:  # the baseline is expected to crash on malformed anchors
        print("%-40s EXCEPTION %s" % (name, type(e).__name__))


def main():
    for name, anchors in CASES:
        run_one(name, anchors)
    # c08: the claim hash must depend on the issue snapshot (same length, same anchor offsets, different body)
    a = (b"IndexError at start " + b"x" * 10)
    b = (b"IndexError at start " + b"y" * 10)
    ca = check_claim(claim([TYPE]), a)["claim_sha256"]
    cb = check_claim(claim([TYPE]), b)["claim_sha256"]
    print("%-40s claim_sha256_equal_for_different_bodies=%s" % ("c08_hash_binds_body", ca == cb))
    # c09: the real jinja#843 claim on its real raw body (gitignored local copy)
    body_path = os.path.join(ROOT, "labs", "jinja-843", "issue843.body.md")
    claim_path = os.path.join(ROOT, "labs", "jinja-843", "claim.json")
    if os.path.exists(body_path):
        with open(claim_path, encoding="utf-8") as f:
            c = json.load(f)
        with open(body_path, "rb") as f:
            show("c09_real_jinja_843", check_claim(c, f.read()))
    else:
        print("c09_real_jinja_843 SKIPPED (labs/jinja-843/issue843.body.md missing; run tools/fetch_issue.py)")


if __name__ == "__main__":
    main()
