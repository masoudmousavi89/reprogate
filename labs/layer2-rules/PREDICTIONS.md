# Layer 2 rules (req_003 required fields, req_010 timeout rule): predictions committed BEFORE the code

Founder decisions (2026-10-03): (req_010) option A: any TIMEOUT run on a claim that is not a timeout claim gives
`INCONCLUSIVE / TIMEOUT_NOT_CLAIMED`, as the requirement text says; (req_003) an exception claim without a valid
`exception_type` must not be `READY`. Both change behaviour; both are tested before they are called done.

## 1. req_003: `claims.support()` checks the required fields of an exception claim
State read from the code: `support()` returns `READY` for every `exception` claim (claims.py:45-46). A claim without
`exception_type` becomes READY and ends as `NO_MATCHING_REPRODUCTION_FOUND` because the matcher compares the observed type
with `None` (matcher.py:170): a wrong input looks like a negative result.

Rule (new): an `exception` claim is READY only if `exception_type` is a non-empty string after strip; `message`, when present,
is a string; `location`, when present, is an object whose `file` and `function`, when present, are non-empty strings. Otherwise
`UNSUPPORTED` with a one-sentence note naming the field. Nothing else about claims changes (`wrong_output` rules and the
provenance check are untouched; provenance stays a separate field).

## 2. req_010: any timeout makes the outcome INCONCLUSIVE / TIMEOUT_NOT_CLAIMED
State read from the code: `aggregate()` gives TIMEOUT_NOT_CLAIMED only when no run completed and at least one timed out
(outcome.py:40); with some completed runs the timeouts are ignored. The invariant (invariants.py:135) says the same.
There is no timeout claim kind, so every claim is "non-timeout".

Rule (new), placed after the checks that already dominate (gate/claim not evaluated, REPOSITORY_MODIFIED,
VERIFIER_INTERNAL_ERROR, all runs ENV_FAILURE) and before the minimum-completed check: `timeouts > 0` gives
`INCONCLUSIVE / TIMEOUT_NOT_CLAIMED`. The invariant is relaxed to "at least one TIMEOUT run" (no condition on completed
runs), so bundles written before this change stay valid. `result.schema.json` text is updated the same way.
min_completed (default 3 of 5) is not changed and not tuned: the lab data contains no real flakiness (only the synthetic
a05), so it cannot tune a threshold; this is stated as a finding, not hidden.

## Predictions
| item | predicted |
|---|---|
| exception claim without `exception_type`, empty string, whitespace, non-string | `claim_status` UNSUPPORTED, outcome NOT_EVALUATED/CLAIM_UNSUPPORTED, no run executed, bundle passes the invariants |
| exception claim with a valid type only; with type + message; with type + location file/function | READY as before (all existing tests and Lab #1 rows unchanged) |
| `message` not a string; `location` not an object; `location.file` empty | UNSUPPORTED with a note naming the field |
| `wrong_output` and unknown kinds | unchanged (w10, w11 still NOT_EVALUATED/CLAIM_UNSUPPORTED; `labs/wrong-output/cases.py` same 11 lines) |
| 4 matching runs + 1 TIMEOUT (was SYMPTOM_REPRODUCED) | INCONCLUSIVE / TIMEOUT_NOT_CLAIMED |
| 3 clean runs + 2 TIMEOUT (was NO_MATCHING) | INCONCLUSIVE / TIMEOUT_NOT_CLAIMED |
| 1 TIMEOUT + 4 ENV_FAILURE (all-ENV is false) | INCONCLUSIVE / TIMEOUT_NOT_CLAIMED (was INSUFFICIENT_VALID_RUNS) |
| 5 TIMEOUT | unchanged: INCONCLUSIVE / TIMEOUT_NOT_CLAIMED |
| timeout + REPOSITORY_MODIFIED run | REPOSITORY_MODIFIED still dominates |
| timeout + HARNESS_ERROR run | VERIFIER_INTERNAL_ERROR still dominates |
| old bundles with partial timeouts | still pass `validate_outcome` (invariant relaxed, no new prohibition); replay of such a bundle may give a different outcome than the one recorded: stated, not fixed (no such bundle is committed in this repository) |
| existing tests | all pass except none expected to change; `test_timeouts_never_reproduce` stays valid; new unit tests are added |
| existing Lab #1 oracle rows (host mode, Windows) | unchanged: no lab row has a partial timeout |

Done for the two requirement clauses if the rows hold on Windows. Closing req_003 also needs the full suite green.

Not covered: Linux/Docker for these two changes (the changes are pure Python logic with unit tests; a Linux run is cheap but
not part of this step), tuning of min_completed (impossible with current data), `NEEDS_INFO` (after alpha), replay of old bundles.
