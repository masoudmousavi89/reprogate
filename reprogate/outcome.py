"""Aggregate per-run verdicts into one outcome (schema 0.1-proto, thresholds are heuristics)."""
from . import constants as C

_GATE_REASON = {
    C.GATE_REJECTED: C.REPRODUCER_REJECTED,
    C.GATE_UNSAFE: C.REPRODUCER_UNSAFE,
    C.GATE_NOT_AUDITABLE: C.REPRODUCER_NOT_AUDITABLE,
}


def aggregate(runs, min_completed=3, provenance="VERIFIED", reproducer_status=C.GATE_VALID,
              claim_status="READY"):
    counts = {
        "total": len(runs),
        "completed": sum(1 for r in runs if r["status"] == C.RUN_COMPLETED),
        "env_failures": sum(1 for r in runs if r["status"] == C.RUN_ENV_FAILURE),
        "timeouts": sum(1 for r in runs if r["status"] == C.RUN_TIMEOUT),
        "invalid": sum(1 for r in runs if r["status"] == C.RUN_INVALID),
        "matching": sum(1 for r in runs if r["status"] == C.RUN_COMPLETED and r["symptom_match"]),
        "clean_completion_runs": sum(1 for r in runs if r.get("clean_completion")),
    }
    qualifier = "PROVENANCE_UNVERIFIED" if provenance == "UNVERIFIED_ALLOWED" else None

    def done(outcome, reason):
        return {"outcome": outcome, "outcome_reason": reason, "counts": counts,
                "outcome_qualifier": qualifier, "min_completed": min_completed}

    if reproducer_status != C.GATE_VALID:
        return done(C.NOT_EVALUATED, _GATE_REASON.get(reproducer_status, C.REPRODUCER_REJECTED))
    if claim_status != "READY":
        reason = C.CLAIM_UNSUPPORTED if claim_status == "UNSUPPORTED" else C.CLAIM_NEEDS_INFO
        return done(C.NOT_EVALUATED, reason)
    invalid_reasons = {r.get("invalid_reason") for r in runs if r["status"] == C.RUN_INVALID}
    if C.REPOSITORY_MODIFIED in invalid_reasons:
        return done(C.INCONCLUSIVE, C.REPOSITORY_MODIFIED)
    if "HARNESS_ERROR" in invalid_reasons:
        return done(C.INCONCLUSIVE, C.VERIFIER_INTERNAL_ERROR)
    if runs and counts["env_failures"] == counts["total"]:
        return done(C.NOT_EVALUATED, C.ENVIRONMENT_UNAVAILABLE)
    if counts["timeouts"] > 0:  # req_010: no claim kind is a timeout claim, so any TIMEOUT run makes the result inconclusive
        return done(C.INCONCLUSIVE, C.TIMEOUT_NOT_CLAIMED)
    if counts["completed"] < min_completed:
        return done(C.INCONCLUSIVE, C.INSUFFICIENT_VALID_RUNS)

    m, c = counts["matching"], counts["completed"]
    if m == 0:
        return done(C.NO_MATCHING_REPRODUCTION_FOUND, C.NONE)
    if m == 1:
        return done(C.INCONCLUSIVE, C.SINGLE_MATCH_ONLY)
    if provenance == "INSUFFICIENT":
        return done(C.INCONCLUSIVE, C.CLAIM_PROVENANCE_INSUFFICIENT)
    if m == c:
        return done(C.SYMPTOM_REPRODUCED, C.NONE)
    return done(C.SYMPTOM_REPRODUCED_FLAKY, C.NONE)
