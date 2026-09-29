"""Matcher rules cases (F-033). Pure function calls on classify_run; nothing is executed.

Usage (repo root): py -3.8 labs/matcher-rules/cases.py
Prints one line per case: id | symptom_match | reasons | exception_origin | target_causal_frame
(the last two columns show '-' while the fields do not exist yet).
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from reprogate.matcher import classify_run  # noqa: E402


def frame(index, cls, function, rel=None):
    f = {"index": index, "class": cls, "function": function}
    if rel:
        f["rel_path"] = rel
        f["authentic"] = True
    return f


def obs(exc_type, message, frames, chain=None, raised_by_reproducer=False, phase="trigger"):
    return {"exit_code": 1, "phase": phase,
            "exception": {"type": exc_type, "message": message, "frames": frames, "chain": chain or [],
                          "raised_by_reproducer_statement": raised_by_reproducer}}


LOC = {"file": "lib/core.py", "function": "__setitem__"}
CLAIM_MSG = {"kind": "exception", "exception_type": "ValueError", "message": "value too large", "location": LOC}
CLAIM_NOMSG = {"kind": "exception", "exception_type": "ValueError", "location": LOC}

REPRO = frame(0, "REPRODUCER", "<module>")
OUTER = frame(1, "TARGET", "__setitem__", "lib/core.py")
INNER_HELPER = frame(2, "TARGET", "_helper", "lib/core.py")
INNER_SAME = frame(1, "TARGET", "__setitem__", "lib/core.py")
STDLIB = frame(3, "STDLIB", "popleft")

CASES = [
    ("m01_type_message_innermost_location", CLAIM_MSG, obs("ValueError", "value too large", [REPRO, INNER_SAME])),
    ("m02_message_claim_location_only_on_outer_target_frame", CLAIM_MSG,
     obs("ValueError", "value too large", [REPRO, OUTER, INNER_HELPER])),
    ("m03_messageless_claim_location_only_on_outer_target_frame", CLAIM_NOMSG,
     obs("ValueError", "anything", [REPRO, OUTER, INNER_HELPER])),
    ("m04_messageless_claim_location_on_innermost_target_frame", CLAIM_NOMSG,
     obs("ValueError", "anything", [REPRO, INNER_SAME])),
    ("m05_one_char_claim_message_wrong_exception_message",
     {"kind": "exception", "exception_type": "ValueError", "message": "e", "location": LOC},
     obs("ValueError", "boom", [REPRO, INNER_SAME])),
    ("m06_two_char_claim_message_no_location",
     {"kind": "exception", "exception_type": "ValueError", "message": "ab"},
     obs("ValueError", "xxabxx", [REPRO, INNER_SAME])),
    ("m07_three_char_claim_message_matches", {"kind": "exception", "exception_type": "ValueError", "message": "abc"},
     obs("ValueError", "xxabcxx", [REPRO, INNER_SAME])),
    ("m08_native_raise_inside_target_frame_ends_with_stdlib_frame", CLAIM_MSG,
     obs("ValueError", "value too large", [REPRO, INNER_SAME, frame(2, "STDLIB", "popleft")])),
    ("m09_origin_and_causal_frame_are_different_frames", CLAIM_NOMSG,
     obs("ValueError", "x", [REPRO, OUTER, INNER_HELPER, STDLIB])),
    ("m10_forged_frame_is_rejected", CLAIM_MSG,
     obs("ValueError", "value too large", [REPRO, INNER_SAME, frame(2, "FORGED_TARGET", "__setitem__", "lib/core.py")])),
    ("m11_reproducer_frame_after_target_is_rejected", CLAIM_MSG,
     obs("ValueError", "value too large", [REPRO, INNER_SAME, frame(2, "REPRODUCER", "cb")])),
    ("m12_claim_without_message_and_location_never_matches", {"kind": "exception", "exception_type": "ValueError"},
     obs("ValueError", "x", [REPRO, INNER_SAME])),
    ("m13_interpreter_conversion_cause_frames",
     {"kind": "exception", "exception_type": "RuntimeError", "message": "generator raised StopIteration",
      "location": {"file": "lib/core.py", "function": "gen"}},
     obs("RuntimeError", "generator raised StopIteration", [REPRO, frame(1, "STDLIB", "next_")],
         chain=[{"via": "cause", "type": "StopIteration",
                 "frames": [frame(0, "TARGET", "outerfn", "lib/core.py"), frame(1, "TARGET", "gen", "lib/core.py")]}])),
    ("m14_no_exception", CLAIM_MSG, {"exit_code": 0, "phase": "trigger", "exception": None}),
]


def short(f):
    if not f:
        return "-"
    return "%s#%s:%s" % (f.get("class"), f.get("index"), f.get("function"))


def main():
    for cid, claim, ob in CASES:
        v = classify_run(ob, claim)
        print("%-58s match=%-5s %-52s origin=%-24s causal=%s" % (
            cid, v["symptom_match"], ",".join(sorted(v["reasons"])) or "-",
            short(v.get("exception_origin")) if "exception_origin" in v else "-",
            short(v.get("target_causal_frame")) if "target_causal_frame" in v else "-"))


if __name__ == "__main__":
    main()
