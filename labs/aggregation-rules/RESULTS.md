# Versioned aggregation rules: results (Windows, py -3.8.10, 2026-10-03)

Predictions: `PREDICTIONS.md`, committed first as 808abd7. Code and tests: caa9204. Experiment script: `run_legacy_experiment.py`; its output on a REAL
bundle (`oracle/before` of the Lab #1 oracle run from two SHAs) is in `run-windows-2026-10-03.log`.

## Tests
205 tests OK, 12 skipped (before: 194 OK, 12 skipped). New: `tests/test_aggregation_rules.py` (11 tests). The `labs/result-invariants` cases (15 valid,
16 invalid) and every older test pass unchanged.

## Predictions vs observed
| item | predicted | observed |
|---|---|---|
| bundles written by this version | `aggregation_rules: "2"`, also for `NOT_EVALUATED`; Lab #1 oracle still passes | held (real oracle bundle has `"2"`; ORACLE PASS; tree hashes `dbc9cd7d...` / `bf8ae6f9...` as in F-048; a rejected-gate outcome also carries it) |
| LEGACY, old shape (4 matching + 1 TIMEOUT, SYMPTOM_REPRODUCED) | `inspect` exit 0 with LEGACY line; `verify` PASS, `aggregation_rules: LEGACY`, `legacy_timeout_semantics: true` | held (log: inspect exit 0, LEGACY line, verify `invariants_ok=True same_outcome=True`, flag true) |
| versioned `"2"` with the same shape | `inspect` exit 1 (`TIMEOUT_RULE`); `verify` does not replay | held (inspect exit 1; `invariants_ok=False`, `replay_outcome` None) |
| same shape with the field simply deleted | passes as LEGACY (loophole stated) | held (that is the LEGACY row; it is the stated limit of a marker that can be removed) |
| `"3"`, `1`, `2`, `""`, null, `["2"]` | ENUM violation, exit 1 | held (unit tests; the CLI row with `"3"`: exit 1) |
| `"2"` with REPOSITORY_MODIFIED / VERIFIER_INTERNAL_ERROR + timeout; 5 TIMEOUT; all ENV_FAILURE; gate rejected; claim unsupported | valid | held (unit tests) |
| old tests and the 31 invariant cases | unchanged | held |

No prediction was missed.

## What this does and does not show
- A bundle now says which aggregation rules produced it, so the timeout rule is enforceable for new bundles without rejecting old ones. Of 201 `outcome.json` on the
  maintainer's machine none had `timeouts > 0`, so no real bundle is LEGACY-with-impact today.
- The marker can be deleted by anyone who edits a bundle; hashes are not signatures. An edited bundle without the field is read as LEGACY. Closing that needs signed
  evidence (after the alpha, as ROADMAP says; the `attestation` part of req_011).
- `verify` replays with the CURRENT rules always: a LEGACY bundle whose recorded timeout recurs in the replay fails with `same_outcome` false. This is by design and
  the report only adds the information flag.
- `tool_version` / `schema_version` are unchanged constants (`0.0.1-proto` / `0.1-proto`); a version policy is a separate decision.
- Linux/Docker were not run for this change. The content audit of the bundle (issue snapshot, repository content, attempts, logs) was not done (founder: later, only if the
  requirement is still ambiguous).
