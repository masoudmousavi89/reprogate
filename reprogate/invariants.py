"""Cross-field invariants of an outcome.json (F-029). Stdlib only; schema/result.schema.json documents the contract.

validate_outcome(outcome) returns a list of "CODE: message" strings; an empty list means every invariant holds.
The rules mirror aggregate() in outcome.py, but as implications over the *recorded* fields, so a bundle whose
outcome.json was edited (and hashes.json regenerated) is still caught.
"""
from . import constants as C

OUTCOMES = (C.SYMPTOM_REPRODUCED, C.SYMPTOM_REPRODUCED_FLAKY, C.NO_MATCHING_REPRODUCTION_FOUND,
            C.INCONCLUSIVE, C.NOT_EVALUATED)
RUN_STATUSES = (C.RUN_COMPLETED, C.RUN_ENV_FAILURE, C.RUN_TIMEOUT, C.RUN_INVALID)
GATE_STATUSES = (C.GATE_VALID, C.GATE_REJECTED, C.GATE_UNSAFE, C.GATE_NOT_AUDITABLE)
CLAIM_STATUSES = ("READY", "NEEDS_INFO", "UNSUPPORTED")
PROVENANCE_STATES = ("VERIFIED", "INSUFFICIENT", "UNVERIFIED_ALLOWED")
QUALIFIERS = (None, "PROVENANCE_UNVERIFIED")

# outcome_reason -> the only outcome it may accompany
REASON_OUTCOME = {
    C.NONE: (C.SYMPTOM_REPRODUCED, C.SYMPTOM_REPRODUCED_FLAKY, C.NO_MATCHING_REPRODUCTION_FOUND),
    C.CLAIM_NEEDS_INFO: (C.NOT_EVALUATED,),
    C.CLAIM_UNSUPPORTED: (C.NOT_EVALUATED,),
    C.REPRODUCER_REJECTED: (C.NOT_EVALUATED,),
    C.REPRODUCER_UNSAFE: (C.NOT_EVALUATED,),
    C.REPRODUCER_NOT_AUDITABLE: (C.NOT_EVALUATED,),
    C.ENVIRONMENT_UNAVAILABLE: (C.NOT_EVALUATED,),
    C.CLAIM_PROVENANCE_INSUFFICIENT: (C.INCONCLUSIVE,),
    C.SINGLE_MATCH_ONLY: (C.INCONCLUSIVE,),
    C.TIMEOUT_NOT_CLAIMED: (C.INCONCLUSIVE,),
    C.REPOSITORY_MODIFIED: (C.INCONCLUSIVE,),
    C.VERIFIER_INTERNAL_ERROR: (C.INCONCLUSIVE,),
    C.INSUFFICIENT_VALID_RUNS: (C.INCONCLUSIVE,),
}

GATE_REASON = {
    C.GATE_REJECTED: C.REPRODUCER_REJECTED,
    C.GATE_UNSAFE: C.REPRODUCER_UNSAFE,
    C.GATE_NOT_AUDITABLE: C.REPRODUCER_NOT_AUDITABLE,
}

REQUIRED = ("outcome", "outcome_reason", "outcome_qualifier", "claim_status", "reproducer_status", "run_status",
            "counts", "min_completed", "claim_provenance")
COUNT_KEYS = ("total", "completed", "env_failures", "timeouts", "invalid", "matching", "clean_completion_runs")


def _is_count(x):
    return isinstance(x, int) and not isinstance(x, bool) and x >= 0


def validate_outcome(o):
    v = []
    if not isinstance(o, dict):
        return ["MISSING_FIELD: outcome is not an object"]
    missing = [k for k in REQUIRED if k not in o]
    if missing:
        return ["MISSING_FIELD: %s" % ", ".join(missing)]

    # enums and types
    def enum(name, value, allowed):
        if value not in allowed:
            v.append("ENUM: %s=%r is not one of %s" % (name, value, list(allowed)))
            return False
        return True

    ok = True
    ok &= enum("outcome", o["outcome"], OUTCOMES)
    ok &= enum("outcome_reason", o["outcome_reason"], tuple(REASON_OUTCOME))
    ok &= enum("claim_status", o["claim_status"], CLAIM_STATUSES)
    ok &= enum("reproducer_status", o["reproducer_status"], GATE_STATUSES)
    ok &= enum("claim_provenance", o["claim_provenance"], PROVENANCE_STATES)
    ok &= enum("outcome_qualifier", o["outcome_qualifier"], QUALIFIERS)
    runs, counts, minc = o["run_status"], o["counts"], o["min_completed"]
    if not isinstance(runs, list) or not all(r in RUN_STATUSES for r in runs):
        v.append("ENUM: run_status must be a list of %s" % list(RUN_STATUSES))
        ok = False
    if not isinstance(counts, dict) or not all(_is_count(counts.get(k)) for k in COUNT_KEYS):
        v.append("ENUM: counts must hold non-negative integers for %s" % list(COUNT_KEYS))
        ok = False
    if not _is_count(minc):
        v.append("ENUM: min_completed must be a non-negative integer")
        ok = False
    if not ok:
        return v  # the rules below need well-formed fields

    outcome, reason = o["outcome"], o["outcome_reason"]
    gate, claim, prov = o["reproducer_status"], o["claim_status"], o["claim_provenance"]
    c = counts

    # counts against run_status
    if c["total"] != len(runs):
        v.append("COUNTS_TOTAL: counts.total=%d but run_status has %d entries" % (c["total"], len(runs)))
    tally = {"completed": runs.count(C.RUN_COMPLETED), "env_failures": runs.count(C.RUN_ENV_FAILURE),
             "timeouts": runs.count(C.RUN_TIMEOUT), "invalid": runs.count(C.RUN_INVALID)}
    for k, n in tally.items():
        if c[k] != n:
            v.append("COUNTS_TALLY: counts.%s=%d but run_status has %d" % (k, c[k], n))
    if c["matching"] > c["completed"]:
        v.append("COUNTS_ORDER: matching (%d) exceeds completed (%d)" % (c["matching"], c["completed"]))
    if c["clean_completion_runs"] > c["completed"]:
        v.append("COUNTS_ORDER: clean_completion_runs (%d) exceeds completed (%d)"
                 % (c["clean_completion_runs"], c["completed"]))

    # outcome <-> reason
    if outcome in OUTCOMES and outcome not in REASON_OUTCOME.get(reason, ()):
        v.append("REASON_OUTCOME: outcome_reason %s cannot accompany outcome %s" % (reason, outcome))

    # gate and claim links
    if gate != C.GATE_VALID:
        if reason != GATE_REASON[gate]:
            v.append("GATE_LINK: reproducer_status %s requires outcome_reason %s (got %s)" % (gate, GATE_REASON[gate], reason))
        if outcome != C.NOT_EVALUATED:
            v.append("GATE_LINK: reproducer_status %s requires outcome NOT_EVALUATED (got %s)" % (gate, outcome))
        if c["total"] != 0:
            v.append("GATE_LINK: a reproducer that did not pass the gate must have no runs (total=%d)" % c["total"])
    else:
        if reason in GATE_REASON.values():
            v.append("GATE_LINK: outcome_reason %s requires a reproducer_status other than VALID" % reason)
        if claim != "READY":
            want = C.CLAIM_UNSUPPORTED if claim == "UNSUPPORTED" else C.CLAIM_NEEDS_INFO
            if reason != want or outcome != C.NOT_EVALUATED:
                v.append("CLAIM_LINK: claim_status %s requires NOT_EVALUATED/%s" % (claim, want))
        elif reason in (C.CLAIM_UNSUPPORTED, C.CLAIM_NEEDS_INFO):
            v.append("CLAIM_LINK: outcome_reason %s requires claim_status other than READY" % reason)
        rr = o.get("runs_requested")
        if claim == "READY" and rr is not None and c["total"] != rr:
            v.append("COUNTS_TOTAL: counts.total=%d but runs_requested=%r" % (c["total"], rr))

    # reason-specific requirements (only meaningful when gate passed and claim is READY)
    if gate == C.GATE_VALID and claim == "READY":
        if reason == C.ENVIRONMENT_UNAVAILABLE:
            if not (c["total"] > 0 and all(r == C.RUN_ENV_FAILURE for r in runs) and c["env_failures"] == c["total"]):
                v.append("ENV_LINK: ENVIRONMENT_UNAVAILABLE requires at least one run and every run ENV_FAILURE")
        if reason in (C.REPOSITORY_MODIFIED, C.VERIFIER_INTERNAL_ERROR) and c["invalid"] < 1:
            v.append("RUN_LINK: %s requires at least one INVALID run" % reason)
        if reason == C.TIMEOUT_NOT_CLAIMED and not (c["completed"] == 0 and c["timeouts"] > 0):
            v.append("RUN_LINK: TIMEOUT_NOT_CLAIMED requires no completed run and at least one TIMEOUT")
        if reason == C.INSUFFICIENT_VALID_RUNS and not c["completed"] < minc:
            v.append("COUNTS_ORDER: INSUFFICIENT_VALID_RUNS requires completed (%d) < min_completed (%d)"
                     % (c["completed"], minc))
        if reason == C.SINGLE_MATCH_ONLY and not (c["matching"] == 1 and c["completed"] >= minc):
            v.append("COUNTS_ORDER: SINGLE_MATCH_ONLY requires exactly 1 matching run and completed >= min_completed")
        if reason == C.CLAIM_PROVENANCE_INSUFFICIENT:
            if not (c["matching"] >= 2 and c["completed"] >= minc):
                v.append("COUNTS_ORDER: CLAIM_PROVENANCE_INSUFFICIENT requires >= 2 matching runs and completed >= min_completed")
            if prov != "INSUFFICIENT":
                v.append("PROVENANCE: CLAIM_PROVENANCE_INSUFFICIENT requires claim_provenance INSUFFICIENT")
        if outcome == C.NO_MATCHING_REPRODUCTION_FOUND and not (c["matching"] == 0 and c["completed"] >= minc):
            v.append("COUNTS_ORDER: NO_MATCHING_REPRODUCTION_FOUND requires 0 matching runs and completed >= min_completed")
        if outcome == C.SYMPTOM_REPRODUCED and not (c["matching"] == c["completed"] and c["matching"] >= 2
                                                    and c["completed"] >= minc):
            v.append("COUNTS_ORDER: SYMPTOM_REPRODUCED requires matching == completed, at least 2, and completed >= min_completed")
        if outcome == C.SYMPTOM_REPRODUCED_FLAKY and not (2 <= c["matching"] < c["completed"] and c["completed"] >= minc):
            v.append("COUNTS_ORDER: SYMPTOM_REPRODUCED_FLAKY requires 2 <= matching < completed and completed >= min_completed")
    if outcome in (C.SYMPTOM_REPRODUCED, C.SYMPTOM_REPRODUCED_FLAKY) and prov == "INSUFFICIENT":
        v.append("PROVENANCE: %s cannot be reported with claim_provenance INSUFFICIENT" % outcome)

    # qualifier and oracle flag
    if (o["outcome_qualifier"] == "PROVENANCE_UNVERIFIED") != (prov == "UNVERIFIED_ALLOWED"):
        v.append("QUALIFIER: outcome_qualifier PROVENANCE_UNVERIFIED must be set exactly when claim_provenance is UNVERIFIED_ALLOWED")
    if o.get("oracle_required") is True and outcome not in (C.SYMPTOM_REPRODUCED, C.SYMPTOM_REPRODUCED_FLAKY):
        v.append("ORACLE: oracle_required is true but the outcome is %s" % outcome)
    return v
