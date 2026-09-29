"""Result invariants cases (F-029). Pure function calls; nothing is executed.

Usage (repo root): py -3.8 labs/result-invariants/cases.py
Valid cases are built with the real aggregate(); invalid ones are hand-made mutations of a valid outcome.
Prints one line per case: id | result | violation codes (or NO_VALIDATOR before reprogate/invariants.py exists).
"""
import copy
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from reprogate import constants as C  # noqa: E402
from reprogate.outcome import aggregate  # noqa: E402

try:
    from reprogate.invariants import validate_outcome  # noqa: E402
except ImportError:
    validate_outcome = None


def run(status=C.RUN_COMPLETED, match=False, clean=False, invalid=None):
    return {"status": status, "symptom_match": match, "clean_completion": clean, "invalid_reason": invalid}


def build(runs, provenance="VERIFIED", gate=C.GATE_VALID, claim="READY", min_completed=3, requested=None,
          oracle_required=None):
    agg = aggregate(runs, min_completed=min_completed, provenance=provenance, reproducer_status=gate,
                    claim_status=claim)
    o = {"outcome": agg["outcome"], "outcome_reason": agg["outcome_reason"],
         "outcome_qualifier": agg["outcome_qualifier"], "claim_status": claim, "reproducer_status": gate,
         "run_status": [r["status"] for r in runs], "counts": agg["counts"], "min_completed": min_completed,
         "runs_requested": len(runs) if requested is None else requested, "claim_provenance": provenance}
    if oracle_required is None:
        oracle_required = o["outcome"] in (C.SYMPTOM_REPRODUCED, C.SYMPTOM_REPRODUCED_FLAKY)
    o["oracle_required"] = oracle_required
    return o


M, N, CL = run(match=True), run(), run(clean=True)
E, T = run(C.RUN_ENV_FAILURE), run(C.RUN_TIMEOUT)

VALID = [
    ("v01_all_match", build([M] * 5)),
    ("v02_flaky", build([M] * 3 + [N] * 2)),
    ("v03_single_match", build([M] + [N] * 4)),
    ("v04_no_match", build([CL] * 5)),
    ("v05_match_plus_env_failures", build([M] * 3 + [E] * 2)),
    ("v06_all_env_failure", build([E] * 5)),
    ("v07_too_few_valid", build([M] * 2 + [E] * 3)),
    ("v08_timeouts_only", build([T] * 5)),
    ("v09_repo_modified", build([run(C.RUN_INVALID, invalid=C.REPOSITORY_MODIFIED)] * 5)),
    ("v10_gate_rejected", build([], gate=C.GATE_REJECTED, requested=5)),
    ("v11_provenance_insufficient", build([M] * 5, provenance="INSUFFICIENT")),
    ("v12_provenance_unverified_allowed", build([CL] * 5, provenance="UNVERIFIED_ALLOWED")),
    ("v13_harness_error", build([run(C.RUN_INVALID, invalid="HARNESS_ERROR")] * 5)),
    ("v14_claim_unsupported", build([], claim="UNSUPPORTED", requested=5)),
    ("v15_inside_oracle_flag_false", build([M] * 5, oracle_required=False)),
]


def mutate(base, **changes):
    o = copy.deepcopy(base)
    for k, v in changes.items():
        if k.startswith("counts_"):
            o["counts"][k[len("counts_"):]] = v
        else:
            o[k] = v
    return o


base_all = build([M] * 5)
base_no = build([CL] * 5)
base_flaky = build([M] * 3 + [N] * 2)
base_env = build([E] * 5)
del_counts = copy.deepcopy(base_all)
del del_counts["counts"]

INVALID = [
    ("i01_reproduced_with_insufficient_runs_reason", mutate(base_all, outcome_reason=C.INSUFFICIENT_VALID_RUNS)),
    ("i02_not_evaluated_with_none", mutate(base_env, outcome_reason=C.NONE)),
    ("i03_inconclusive_with_none", mutate(build([M] + [N] * 4), outcome_reason=C.NONE)),
    ("i04_no_match_with_two_matching", mutate(base_no, counts_matching=2)),
    ("i05_reproduced_matching_not_all_completed", mutate(base_all, counts_matching=3)),
    ("i06_flaky_with_all_matching", mutate(base_flaky, counts_matching=5)),
    ("i07_total_differs_from_run_status", mutate(base_all, counts_total=4)),
    ("i08_completed_differs_from_run_status_tally", mutate(base_all, counts_completed=4)),
    ("i09_env_unavailable_with_completed_run", mutate(base_env, run_status=["ENV_FAILURE"] * 4 + ["COMPLETED"])),
    ("i10_reproduced_with_insufficient_provenance", mutate(base_all, claim_provenance="INSUFFICIENT")),
    ("i11_unverified_qualifier_with_verified_provenance", mutate(base_no, outcome_qualifier="PROVENANCE_UNVERIFIED")),
    ("i12_gate_rejected_but_no_match_outcome", mutate(base_no, reproducer_status=C.GATE_REJECTED)),
    ("i13_unknown_outcome_value", mutate(base_all, outcome="SYMPTOM_CONFIRMED")),
    ("i14_counts_missing", del_counts),
    ("i15_oracle_required_with_no_match", mutate(base_no, oracle_required=True)),
    ("i16_reproduced_with_single_matching_run", mutate(build([M, E, E, E, E], min_completed=1), outcome=C.SYMPTOM_REPRODUCED,
                                                      outcome_reason=C.NONE)),
]


def show(cid, o):
    if validate_outcome is None:
        print("%-52s NO_VALIDATOR" % cid)
        return None
    v = validate_outcome(o)
    codes = sorted({x.split(":", 1)[0] for x in v})
    print("%-52s %-8s %s" % (cid, "VALID" if not v else "INVALID", ",".join(codes)))
    return v


def main():
    bad_valid = bad_invalid = 0
    for cid, o in VALID:
        v = show(cid, o)
        bad_valid += 1 if v else 0
    for cid, o in INVALID:
        v = show(cid, o)
        bad_invalid += 0 if v else 1
    if validate_outcome is not None:
        print("false rejects among valid: %d | false accepts among invalid: %d" % (bad_valid, bad_invalid))


if __name__ == "__main__":
    main()
