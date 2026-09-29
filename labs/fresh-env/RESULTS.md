# Fresh environment per run: results (2026-09-29; predictions in PREDICTIONS.md, committed first as 0a3343d)

Windows 11, Python 3.8.10, host mode, Lab #1 pair (`MarkupSafe==2.0.1`), d01-d03 from `labs/adversarial-round3/` against a copy of
the venv used as `--env-template`. Evidence folder deleted afterwards (personal paths).

| item | predicted | observed |
|---|---|---|
| d01 | NO_MATCHING/NONE, 5 COMPLETED; template file hash unchanged; recorded mode FRESH_COPY_PER_RUN and template hash equal to an independent hash | as predicted (`template_file_hash_unchanged=True`, `recorded_hash_equals_independent=True`) |
| d02 | marker length 0; NO_MATCHING/NONE | `marker_writes=0`; NO_MATCHING/NONE, 5 COMPLETED |
| d03 | 5 COMPLETED and 5 clean completions | `completed=5 clean_completion_runs=5` (F-028 shared environment: 1) |
| template after all attacks | unchanged | tree hash identical before and after d01, d01 again, d02, d03 |
| determinism | same template hash and outcome for two evaluations | `same_template_hash=True`; same outcome |
| jinja oracle, real `.venv` as read-only template | ORACLE PASS, invariants OK, real `.venv` untouched | oracle_pass True (before SYMPTOM_REPRODUCED, after NO_MATCHING/clean completion), 2 of 2 bundles `invariants: OK`, real `.venv` tree hash unchanged |
| cost | "a few seconds per run" (a guess) | `env_copy_seconds` about 1.0-1.6 s per run for a ~17 MB venv (averages 1.08, 1.46, 1.38, 1.38); total 10-13 s per 5-run evaluation including the two tree hashes per run and the 5 runs themselves; jinja oracle (10 runs) 24 s. No same-machine baseline time for the shared mode was measured, so the added cost is not isolated |
| unit tests | existing pass, new file passes | 107 tests OK (100 + 7 new in `tests/test_fresh_env.py`), 11 skipped |

All predictions held. Limits: the cost was measured on one small venv on an SSD-class disk; larger environments will cost more and
the copy is a full copy (no hard links or caching); Linux host mode with a template and a template that cannot be copied were not
tested; the run of `run_fresh_env.ps1` printed the CLI outcome lines only after the script was fixed (`Measure-Command` swallowed
them); the values above come from the evidence files.

## F-038 test fix: results (predictions in PREDICTIONS.md, committed first as 90d2287)

| item | prediction | observed |
|---|---|---|
| Windows, full suite | 136 OK, 11 skipped | 136 OK, 11 skipped |
| Windows, `tests/test_fresh_env.py` | 7 of 7 OK | 7 of 7 OK |
| Linux, `tests/test_fresh_env.py` and full suite | 7 of 7; 136 OK, 0 skipped | 7 of 7 OK (1.1 s); full suite Ran 136, OK, 0 skipped (uv CPython 3.8.20, root, Docker image present) |
