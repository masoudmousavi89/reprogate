# Hash problems in inspect, structure check in verify: results (2026-09-29; predictions in PREDICTIONS.md, committed first as 9405b74)

Windows 11, Python 3.8.10, host mode. No reproducer was executed by `cases.py`.

| item | prediction | observed |
|---|---|---|
| baseline (code after F-035), 15 cases | h01-h04 exit 0, h05 exit 1, h06 CRASH JSONDecodeError, h07 exit 2 (generic), h08-h09 CRASH AttributeError, h10-h11 CRASH KeyError, h12-h13 CRASH FileNotFoundError, h14 CRASH AttributeError, h15 CRASH KeyError | all 15 as predicted |
| after the change, 15 cases | h01-h03 exit 1; h04-h07 exit 2 INVALID_BUNDLE; h08-h09 exit 1; h10-h15 exit 1, VERIFY FAIL, problem named | all 15 as predicted; messages: `hash mismatch: gate.json`, `unrecorded file: extra.txt`, `missing file: gate.json` (with `invariants: OK`), `missing hashes.json`, `hashes.json is not valid JSON`, `hashes.json has no files object`, `STRUCTURE: environment.json has no git.commit`, `... reproducer_name is not a plain file name: None`, `missing reproducer/r.py`, `... not a plain file name: '../missing.py'`, `claim.json has no claim object`, `runs_requested is not an integer >= 1` |
| F-035 cases | all 15 keep their results | all 15 unchanged |
| unit tests | existing 131 pass; new tests | 136 tests OK (131 + 5 new in `tests/test_bundle_structure.py`), 11 skipped; `verify` through the CLI on a complete synthetic bundle still exit 0 (F-035 test) |
| real local bundles (14) | 13 unchanged with no structure problem; `f04_subclass_override` exit 2 naming outcome.json and hashes.json | 13 with exit 0, byte-identical `inspect` output and `structure_problems` empty; `f04_subclass_override`: exit 2, `INVALID_BUNDLE: missing outcome.json; missing hashes.json` |

All predictions held. Not covered: Linux and Docker; malformed values inside a claim object, which `evaluate` handles like
any user claim.
