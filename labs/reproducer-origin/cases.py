"""Reproducer origin evidence cases (F-043). Runs on a SYNTHETIC library (tests/helpers.py), no network.

Usage (repo root): py -3.8 labs/reproducer-origin/cases.py
Prints one line per case: case | result.
"""
import copy
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from reprogate.evidence import verify_hashes  # noqa: E402
from reprogate.invariants import validate_outcome  # noqa: E402
from reprogate.pipeline import evaluate, replay  # noqa: E402
from tests import helpers as H  # noqa: E402

FAST = dict(runs=3, timeout=20, min_completed=3)
TMP = tempfile.mkdtemp(prefix="rg-origin-")
BUGGY = H.make_repo(os.path.join(TMP, "buggy"))
CLAIM = H.verified_claim()
REPRO = H.write_repro(TMP, "repro.py", H.GOOD_REPRO)
SRC_DIFFERENT = H.write_repro(TMP, "src_different.txt", ">>> from minilib import Box\n>>> b = Box(1)\n")
SRC_IDENTICAL = H.write_repro(TMP, "src_identical.txt", H.GOOD_REPRO)
SRC_ONE_BYTE = H.write_repro(TMP, "src_one_byte.txt", H.GOOD_REPRO + b"\n")


def run(name, **kw):
    out = os.path.join(TMP, "ev-" + name)
    try:
        o = evaluate(BUGGY, H.PYTHON, CLAIM, REPRO, out, **dict(FAST, **kw))
    except TypeError:
        return "TypeError", out
    except ValueError:
        return "ValueError (outcome.json written: %s)" % os.path.exists(os.path.join(out, "outcome.json")), out
    has = lambda p: os.path.isfile(os.path.join(out, p))
    diff_nonempty = has("origin/adaptation.diff") and os.path.getsize(os.path.join(out, "origin/adaptation.diff")) > 0
    return ("ok evidence=%s source_file=%s diff_file=%s diff_nonempty=%s source_sha=%s diff_sha=%s" % (
        o.get("reproducer_origin_evidence"), has("origin/source.txt"), has("origin/adaptation.diff"), diff_nonempty,
        "reproducer_origin_source_sha256" in o, "reproducer_origin_diff_sha256" in o)), out


def main():
    lines = []
    cases = [
        ("o00_adapted_no_source", dict(origin="AGENT_ADAPTED")),
        ("o01_adapted_with_different_source", dict(origin="AGENT_ADAPTED", origin_source=SRC_DIFFERENT)),
        ("o02_adapted_with_identical_source", dict(origin="AGENT_ADAPTED", origin_source=SRC_IDENTICAL)),
        ("o03_verbatim_identical_source", dict(origin="ISSUE_VERBATIM_SNIPPET", origin_source=SRC_IDENTICAL)),
        ("o04_verbatim_one_byte_different", dict(origin="ISSUE_VERBATIM_SNIPPET", origin_source=SRC_ONE_BYTE)),
        ("o05_verbatim_no_source", dict(origin="ISSUE_VERBATIM_SNIPPET")),
        ("o06_human_authored_no_source", dict(origin="HUMAN_AUTHORED")),
        ("o07_agent_authored_with_source", dict(origin="AGENT_AUTHORED", origin_source=SRC_IDENTICAL)),
    ]
    outs = {}
    for name, kw in cases:
        res, out = run(name, **kw)
        outs[name] = out
        lines.append((name, res))
    b = outs["o01_adapted_with_different_source"]
    # o08: the diff edited after the run is caught by the bundle hashes
    dp = os.path.join(b, "origin", "adaptation.diff")
    if os.path.isfile(dp):
        keep = open(dp, "rb").read()
        with open(dp, "ab") as f:
            f.write(b"# edited\n")
        ok, problems = verify_hashes(b)
        with open(dp, "wb") as f:
            f.write(keep)
        lines.append(("o08_diff_edited_after_the_run", "hashes_ok=%s problems=%d" % (ok, len(problems))))
    else:
        lines.append(("o08_diff_edited_after_the_run", "no bundle with a diff"))
    # o09: replay of that bundle
    if os.path.isfile(os.path.join(b, "outcome.json")):
        try:
            rep = replay(b, BUGGY, H.PYTHON, runs=3)
            lines.append(("o09_replay_of_the_adapted_bundle", "hashes_ok=%s same_outcome=%s" % (rep.get("hashes_ok"), rep.get("same_outcome"))))
        except Exception as e:  # the baseline has nothing to replay with a source
            lines.append(("o09_replay_of_the_adapted_bundle", type(e).__name__))
    # o10: invariants on a recorded outcome
    base_path = os.path.join(b, "outcome.json")
    if os.path.isfile(base_path) and "reproducer_origin_evidence" in json.load(open(base_path)):
        base = json.load(open(base_path))

        def viol(mut):
            o = copy.deepcopy(base)
            mut(o)
            return "violations=%d" % len(validate_outcome(o))
        lines.append(("o10a_consistent_record", viol(lambda o: None)))
        lines.append(("o10b_diff_sha_removed", viol(lambda o: o.pop("reproducer_origin_diff_sha256"))))
        lines.append(("o10c_unknown_evidence_value", viol(lambda o: o.update(reproducer_origin_evidence="BOGUS"))))

        def old_style(o):
            for k in ("reproducer_origin_evidence", "reproducer_origin_source_sha256", "reproducer_origin_diff_sha256"):
                o.pop(k, None)
        lines.append(("o10d_old_record_without_the_fields", viol(old_style)))
        lines.append(("o10e_identical_but_source_sha_differs", viol(lambda o: o.update(
            reproducer_origin_evidence="IDENTICAL_TO_SOURCE", reproducer_origin_source_sha256="0" * 64))))
    else:
        lines.append(("o10_invariants", "no outcome with the new fields"))
    for name, res in lines:
        print("%-42s %s" % (name, res))


if __name__ == "__main__":
    main()
