# Incomplete and unreadable bundles: results (2026-09-29; predictions in PREDICTIONS.md, committed first as 24cd653)

Windows 11, Python 3.8.10, host mode. No reproducer was executed by `cases.py`.

| item | prediction | observed |
|---|---|---|
| baseline (code after F-034), 15 cases | b01-b07 CRASH, b08 exit 0, b09-b11 exit 1, b12-b13 CRASH, b14 exit 1, b15 exit 2 | 14 of 15 as predicted. **Miss: b13** (environment.json not valid JSON, hashes regenerated) gave exit 2, not a crash: `verify` already catches `ValueError`, and `JSONDecodeError` is one, so it printed `ERROR:` and returned 2 |
| after the change, 15 cases | b01-b05 and b10-b13, b15 exit 2 with INVALID_BUNDLE; b06 exit 1 (MISSING_FIELD); b07 exit 0 (`sandbox: -`); b08 exit 0; b09, b14 exit 1 | all 15 as predicted; messages name the problem (`evidence path is not a folder`, `missing outcome.json; missing environment.json`, `environment.json is not valid JSON`) |
| unit tests | existing 127 pass; new tests | 131 tests OK (127 + 4 new in `tests/test_incomplete_bundle.py`), 11 skipped; `verify` through the CLI on a complete synthetic bundle: exit 0, VERIFY PASS |
| real local bundles (14, ignored folders) | 13 unchanged, `f04_subclass_override` of the first folder exit 2 | 13 with exit 0, `invariants: OK` and byte-identical `inspect` output before and after; `f04_subclass_override` (claim, gate, reproducer only): traceback and exit 1 before, `INVALID_BUNDLE: missing outcome.json` and exit 2 after |

The b13 miss is recorded, not tuned: the prediction was wrong about the old code, the new behaviour for b13 is as predicted
(exit 2, now with the INVALID_BUNDLE message instead of a generic `ERROR:`).

Not covered (unchanged, see PREDICTIONS.md): `inspect` ignores hash problems in its exit code; `verify` can still crash on
readable JSON with missing keys or on a missing reproducer file when `hashes.json` was regenerated. Linux and Docker were
not run.
