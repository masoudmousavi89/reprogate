"""Nested-scope location cases (F-034, decision_056). Pure function calls; nothing is executed.

Usage (repo root): py -3.8 labs/nested-scope/cases.py
Each case is a synthetic observation whose innermost frame is a nested scope (or not). `enclosing_function` is the field the
supervisor will write from the AST once the change exists; the old code ignores it.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from reprogate.matcher import classify_run  # noqa: E402

CLAIM = {"kind": "exception", "exception_type": "KeyError",
         "location": {"file": "lib/dict.py", "function": "__eq__"}}
CLAIM_MSG = {"kind": "exception", "exception_type": "KeyError", "message": "'a'",
             "location": {"file": "lib/dict.py", "function": "__eq__"}}
CLAIM_NESTED = {"kind": "exception", "exception_type": "KeyError",
                "location": {"file": "lib/dict.py", "function": "<genexpr>"}}


def frame(index, cls, function, rel=None, enclosing=None):
    f = {"index": index, "class": cls, "function": function}
    if rel:
        f["rel_path"] = rel
        f["authentic"] = True
    if enclosing is not None:
        f["enclosing_function"] = enclosing
    return f


REPRO = frame(0, "REPRODUCER", "<module>")
EQ = frame(1, "TARGET", "__eq__", "lib/dict.py")


def obs(frames):
    return {"exit_code": 1, "phase": "trigger",
            "exception": {"type": "KeyError", "message": "'a'", "frames": frames, "chain": [],
                          "raised_by_reproducer_statement": False}}


CASES = [
    ("n01_genexpr_inside_eq_claim_names_eq", CLAIM,
     obs([REPRO, EQ, frame(2, "TARGET", "<genexpr>", "lib/dict.py", "__eq__")])),
    ("n02_listcomp_inside_eq", CLAIM, obs([REPRO, EQ, frame(2, "TARGET", "<listcomp>", "lib/dict.py", "__eq__")])),
    ("n03_lambda_inside_eq", CLAIM, obs([REPRO, EQ, frame(2, "TARGET", "<lambda>", "lib/dict.py", "__eq__")])),
    ("n04_genexpr_enclosed_by_other_function", CLAIM,
     obs([REPRO, EQ, frame(2, "TARGET", "<genexpr>", "lib/dict.py", "other")])),
    ("n05_local_named_function_is_not_a_nested_scope", CLAIM,
     obs([REPRO, EQ, frame(2, "TARGET", "helper", "lib/dict.py", "__eq__")])),
    ("n06_forged_nested_frame", CLAIM,
     obs([REPRO, EQ, frame(2, "FORGED_TARGET", "<genexpr>", "lib/dict.py", "__eq__")])),
    ("n07_nested_frame_without_enclosing_function", CLAIM,
     obs([REPRO, EQ, frame(2, "TARGET", "<genexpr>", "lib/dict.py")])),
    ("n08_claim_names_the_nested_scope_itself", CLAIM_NESTED,
     obs([REPRO, EQ, frame(2, "TARGET", "<genexpr>", "lib/dict.py", "__eq__")])),
    ("n09_file_mismatch_even_if_enclosing_matches", CLAIM,
     obs([REPRO, EQ, frame(2, "TARGET", "<genexpr>", "lib/other.py", "__eq__")])),
    ("n10_nested_frame_is_not_the_innermost", CLAIM,
     obs([REPRO, EQ, frame(2, "TARGET", "<genexpr>", "lib/dict.py", "__eq__"),
          frame(3, "TARGET", "helper", "lib/dict.py")])),
    ("n11_message_claim_nested_location", CLAIM_MSG,
     obs([REPRO, EQ, frame(2, "TARGET", "<genexpr>", "lib/dict.py", "__eq__")])),
    ("n12_plain_frame_unchanged", CLAIM, obs([REPRO, EQ])),
]


def main():
    for cid, claim, ob in CASES:
        v = classify_run(ob, claim)
        print("%-52s match=%-5s %s" % (cid, v["symptom_match"], ",".join(sorted(v["reasons"])) or "-"))


if __name__ == "__main__":
    main()
