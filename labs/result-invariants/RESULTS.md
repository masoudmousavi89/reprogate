# Result invariants: results (2026-09-29; predictions in PREDICTIONS.md, committed first as c31317b)

Windows 11, Python 3.8.10. Evidence folder of this run deleted (personal paths).

| check | prediction | observed |
|---|---|---|
| baseline, before `reprogate/invariants.py` | 31 x NO_VALIDATOR | 31 x NO_VALIDATOR |
| 15 valid outcomes from the real `aggregate()` | all VALID | all VALID (0 false rejects) |
| 16 impossible mutations | all INVALID with the listed primary code | all INVALID (0 false accepts), every primary code present; extra codes appeared on i01 (COUNTS_ORDER), i08 (COUNTS_ORDER), i09 (COUNTS_TALLY) |
| unit tests | existing pass, new file covers the cases | 100 tests OK (91 + 9 new), 11 skipped (5 POSIX-only, 6 Docker) |
| Lab #1 runner | 6 of 6 rows unchanged, all bundles pass | 6 of 6 rows unchanged; 7 bundles (oracle before/after, case_c, f01-f04) all `invariants: OK` and `inspect` exit 0. The prediction said 8 bundles: that count was wrong (2 + 1 + 4 = 7) |
| `verify` on a real bundle | PASS, `invariants_ok: true` | VERIFY PASS, exit 0 |
| `verify` on a copy with an impossible `outcome_reason` and regenerated `hashes.json` | FAIL, non-zero, violation printed | VERIFY FAIL, exit 1; `hashes_ok` true, `replay_outcome` null (not replayed); REASON_OUTCOME and COUNTS_ORDER printed |

Older bundles (not predicted in detail): two earlier evidence folders from the same day (before F-021..F-027) hold 14
bundles; 13 pass `inspect` with `invariants: OK`. One (`f04_subclass_override` of the first folder) has no `outcome.json` at all
(an interrupted earlier run, unrelated to this change), so `inspect` stops with a `FileNotFoundError` traceback and exit 1: the
tool fails, but not cleanly. Recorded, not changed here.

Not covered: bundles from before F-021 (no `oracle_required` field; the check is skipped when the key is absent, and tested
only on a synthetic dict); Docker-mode bundles; `claim_status` other than READY from a real run (the pipeline never produces
it; a Claim Extractor is a real dependency).

## Linux run (2026-09-29): `cases.py` and Linux jinja bundles

`python3.8 labs/result-invariants/cases.py`: 15 of 15 valid outcomes VALID, 16 of 16 impossible ones INVALID with the
predicted primary codes, `false rejects among valid: 0 | false accepts among invalid: 0`. Matches PREDICTIONS.md.

Prediction "Linux jinja bundles" (committed in 500a517): `run_lab001.sh` on Linux, host mode, unverified provenance.
Result: 7 bundles (oracle before/after, case_c_unpinned, f01-f04); `inspect --evidence` exit 0 and `invariants: OK` for all 7;
`verify` on `oracle/before` (host mode, pinned venv): `VERIFY PASS`, exit 0, commit and environment match, replay outcome
SYMPTOM_REPRODUCED. Deviation in wording, not in substance: the prediction spoke of `provenance_sufficient` staying False; bundles do not
store that field, they store `claim_provenance: UNVERIFIED_ALLOWED`, `provenance_verified: false` and the qualifier `PROVENANCE_UNVERIFIED`,
which is the valid combination the prediction meant. Own mistake during the run: the first `inspect` calls omitted `--evidence`
(usage error, exit 2, no bundle involved); repeated correctly.
