# Layer 2 rules: results (Windows, py -3.8.10, 2026-10-03)

Predictions: `PREDICTIONS.md`, committed first as 720bc65. Code and tests: e1469c0. Corpus fixture and index: 7678108 and the
commit after it (`labs/adversarial-corpus/`).

## Tests
194 tests OK, 12 skipped (before: 184 OK, 12 skipped). New: `tests/test_layer2_rules.py` (10 tests). Existing outcome, invariant and
end-to-end tests pass unchanged, including `test_timeouts_never_reproduce` and the 15 valid / 16 invalid invariant cases.

## Predictions vs observed
| item | predicted | observed |
|---|---|---|
| exception claim without `exception_type`, empty, whitespace, non-string | UNSUPPORTED, NOT_EVALUATED/CLAIM_UNSUPPORTED, no run, invariants valid | held (unit tests over 7 inputs; one real `evaluate` without a type: `claim_status` UNSUPPORTED, no runs, note names `exception_type`, `validate_outcome` empty) |
| valid claims (type only, type + message, type + location parts) | READY as before | held |
| bad `message`, bad `location`, empty `location.file`, `location.function` None | UNSUPPORTED naming the field | held |
| `wrong_output` and unknown kinds | unchanged | held (`labs/wrong-output/cases.py`: the same 11 lines as before, w10 and w11 NOT_EVALUATED/CLAIM_UNSUPPORTED) |
| 4 matching + 1 TIMEOUT; 3 clean + 2 TIMEOUT; 1 TIMEOUT + 4 ENV_FAILURE; 3 matching + 1 other + 1 TIMEOUT | INCONCLUSIVE / TIMEOUT_NOT_CLAIMED | held (the first was SYMPTOM_REPRODUCED, the second NO_MATCHING, the third INSUFFICIENT_VALID_RUNS, the fourth FLAKY before the change) |
| 5 TIMEOUT | unchanged | held |
| REPOSITORY_MODIFIED, HARNESS_ERROR, unsupported claim, rejected gate | still dominate | held |
| invariants | new shape (some completed) and old shape accepted; a lie (TIMEOUT_NOT_CLAIMED with no timeout) refused | held |
| Lab #1 oracle from two SHAs (host, real `.venv` template) | unchanged | held: ORACLE PASS, tree hashes `dbc9cd7d...` and `bf8ae6f9...` as in F-048 |
| old bundles with partial timeouts | still valid; replay may differ | not exercised (no such bundle is committed); stated |

No prediction was missed. A side effect worth recording: my first version of the real-run test edited a FROZEN claim and was refused by the
F-042 hash check (`claim changed after freezing`), which is the correct behaviour; the test now uses the unfrozen claim.

## What this does NOT show
- `min_completed` (3 of 5) is unchanged and untuned. The lab data holds no real flakiness (only the synthetic `a05`), so no threshold can be
  derived from it. Tuning needs more real runs.
- Linux/Docker were not run for these two changes (pure Python logic, covered by unit tests).
- `NEEDS_INFO` (needs a Claim Extractor) stays after the alpha.
- Replay of a pre-change bundle that had a partial timeout may produce a different outcome than recorded.
