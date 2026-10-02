# Versioned aggregation rules in the evidence bundle (req_011 replay compatibility): predictions committed BEFORE the code

Question raised by the timeout change of F-054: how do bundles written before it relate to the new rule? Read-only experiment on 2026-10-03: a real
oracle bundle was edited into the old-semantics shape (4 matching + 1 TIMEOUT, outcome `SYMPTOM_REPRODUCED`), `hashes.json` regenerated:
`inspect` exit 0 with `invariants: OK`, `verify` PASS (the replay runs fresh, no timeout recurs, `(outcome, reason)` is equal). Of 201
`outcome.json` files on the maintainer's machine none has `timeouts > 0`. Every one of the 201 has `tool_version 0.0.1-proto` and `schema_version
0.1-proto`, constants that never change, so a bundle does not say which aggregation rules produced it. Consequence: the strict timeout rule
cannot be put into `validate_outcome` without rejecting old bundles, and a bundle with `timeouts > 0` and `SYMPTOM_REPRODUCED` passes `inspect` and
`verify` today.

## Design (founder decision 2026-10-03: option A of req_011)
- `outcome.json` gets an optional field `aggregation_rules`. This version writes `"2"` (rules 1 = everything before F-054, never written; rules 2 =
  any TIMEOUT run gives INCONCLUSIVE / TIMEOUT_NOT_CLAIMED). A bundle WITHOUT the field is `LEGACY`.
- `validate_outcome`: when the field is present it must be `"2"` (anything else, including null, is an ENUM violation); for `"2"` a new invariant
  `TIMEOUT_RULE` applies: with a passed gate and a READY claim, `counts.timeouts > 0` requires `TIMEOUT_NOT_CLAIMED`, unless the reason is
  `REPOSITORY_MODIFIED` or `VERIFIER_INTERNAL_ERROR`, which dominate (as in `aggregate`). A LEGACY bundle is never subject to it.
- `inspect` prints a line `aggregation rules :` with the value, or `LEGACY (no aggregation_rules field: written before F-054; the timeout rule of that
  time may differ)`; exit codes unchanged (LEGACY alone is not a failure).
- `verify` report gets `aggregation_rules` (the recorded value or `LEGACY`) and, for LEGACY, `legacy_timeout_semantics` true when the recorded outcome
  has `timeouts > 0` and is not `TIMEOUT_NOT_CLAIMED` (information, not a failure; the replay itself always uses the current rules, so a recurring
  timeout in the replay makes `same_outcome` false, which is the existing, intended behaviour).
- `schema/result.schema.json` documents the field and the invariant. `tool_version` and `schema_version` are NOT changed here (a version policy is a
  separate decision).

## Predictions
| item | predicted |
|---|---|
| every outcome written by this version (also `NOT_EVALUATED`) | has `aggregation_rules: "2"`; the real Lab #1 oracle bundles pass `inspect` (exit 0) and the oracle still passes |
| LEGACY bundle (field absent), shape of the experiment (4 matching + 1 TIMEOUT, `SYMPTOM_REPRODUCED`) | `inspect` exit 0, line says LEGACY; `verify` PASS, report `aggregation_rules: LEGACY`, `legacy_timeout_semantics: true` |
| versioned `"2"` bundle edited to the same shape | `inspect` exit 1 with `TIMEOUT_RULE`; `verify` refuses to replay (invariants not ok) |
| the same edited shape with the field simply deleted | passes as LEGACY: this loophole is stated, not closed (without a marker the rule cannot be enforced) |
| `aggregation_rules` equal to `"3"`, `1`, `""` or null | ENUM violation, `inspect` exit 1 |
| `"2"` with REPOSITORY_MODIFIED or VERIFIER_INTERNAL_ERROR and a timeout run | valid (they dominate) |
| `"2"` bundle with 5 TIMEOUT, or all runs ENV_FAILURE, or gate rejected, or claim unsupported | valid (no new constraint) |
| old tests (194) | all pass; the `labs/result-invariants` cases (15 valid, 16 invalid) are unchanged; the bundles those cases build with `build()` have no field and stay valid as LEGACY |
| new tests | in `tests/test_aggregation_rules.py` |

Done for this clause of req_011 if the rows hold on Windows. Closing req_011 is a founder decision and also depends on the requirement text (limits stated
in the memory file, not in this lab).

Not covered: Linux/Docker for this change, a version policy for `tool_version` / `schema_version`, forged unversioned bundles (see above), the content audit
of the bundle (issue snapshot, repository content, attempts, logs), attestation (after the alpha).
