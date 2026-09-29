# Linux verification run 2 (F-032..F-036): results (2026-09-29)

Predictions: `PREDICTIONS.md` in this folder, committed and pushed before any run. Linux container (user root), CPython 3.8.20 and 3.12.11
(uv), Docker, image `mirror.gcr.io/library/python:3.8-slim`. Provenance not verifiable here (GitHub API 403, F-010): unverified-provenance
flag, qualifier `PROVENANCE_UNVERIFIED`. Evidence stayed outside the repository (`<HOME>/rg-work`, `<HOME>/reprogate-lab`).

| item | prediction | observed |
|---|---|---|
| A. unit tests | 136 run, 0 failures, 0 errors, 0 skipped | 136 run, **2 failures + 1 error**, 0 skipped: all three in `tests/test_fresh_env.py` (`test_fresh_copy_leaves_the_template_untouched_and_records_the_mode`: `completed` 0 != 3; `test_reproducer_writing_into_the_template_aborts_before_the_next_run`: ValueError not raised; `test_control_without_a_template_the_marker_persists`: FileNotFoundError for `marker.txt`). The other 133 pass, including the 5 POSIX-only and 6 Docker tests. **MISS** |
| B. fresh env (`run_fresh_env.sh`) | d01 NO_MATCHING/5 COMPLETED, template file hash unchanged, mode FRESH_COPY_PER_RUN, recorded hash = independent tree hash; d01 again same; d02 marker 0; d03 5 completed and 5 clean; template unchanged; oracle PASS, 2 of 2 invariants OK, real venv unchanged; symlinks copied as links | all as predicted: d01 NO_MATCHING_REPRODUCTION_FOUND, 5 COMPLETED; `template_file_hash_unchanged=True`; `recorded_mode=FRESH_COPY_PER_RUN`, `recorded_hash_equals_independent=True`; `DETERMINISM same_template_hash=True`; `marker_writes=0`; d03 `completed=5 clean_completion_runs=5`; `TEMPLATE tree_hash_unchanged_after_all_attacks=True`; oracle before SYMPTOM_REPRODUCED, after NO_MATCHING, ORACLE PASS; `REAL_VENV tree_hash_unchanged=True`; before/after `invariants: OK`. Template symlinks: `lib64 -> lib`, `bin/python -> python3.8`, `bin/python3 -> python3.8`, `bin/python3.8 -> <uv python 3.8>`. Copy cost per run 0.06-0.5 s (avg 0.11, 0.26, 0.37, 0.45 s). matches |
| C. jinja-843 (`run_lab001.sh`) | 6 of 6 rows | 6 of 6 rows YES, all bundles `PROVENANCE_UNVERIFIED`. matches |
| D. labs 2-9 host | 33 of 33 rows; sortedcontainers-eq oracle PASS with LOCATION_VIA_NESTED_SCOPE in the before runs | 33 of 33 rows YES (29 rows in 7 labs on 3.8, 4 rows of more-itertools-falsy on 3.12); sortedcontainers-eq oracle PASS, LOCATION_VIA_NESTED_SCOPE in 5 of 5 before runs. matches |
| E. Docker sortedcontainers-eq | before SYMPTOM_REPRODUCED with LOCATION_VIA_NESTED_SCOPE, ORACLE PASS | before SYMPTOM_REPRODUCED, after NO_MATCHING_REPRODUCTION_FOUND, post-fix CLEAN_COMPLETION, ORACLE PASS; LOCATION_VIA_NESTED_SCOPE in 5 of 5 before runs. matches |
| F. F-035/F-036 | cases.py outputs equal the "after" columns (30 lines); inspect exit 0 / invariants OK / hashes OK on every bundle of B-E; verify PASS without STRUCTURE line, host and Docker | both `cases.py` print 15 lines each (30 in total) with the predicted exit codes and INVALID_BUNDLE marks; `inspect` on 63 of 63 bundles: exit 0, `invariants: OK`, `hashes: OK`; `verify` host on jinja oracle/before: PASS, exit 0; `verify --sandbox docker` on docker-sc/before: PASS, exit 0. Both verify outputs contain `"structure_problems": []` (empty list, no problem reported; read as "no STRUCTURE line"). Lines were compared to the predicted exit-code groups, not diffed against the RESULTS.md files. matches |

## Misses
- A: 3 tests of `tests/test_fresh_env.py` fail on this Linux container (running as root, uid 0). The first failure shows 0 of 3 runs COMPLETED in
  a venv created by the test itself; the same fresh-environment mechanism works in B on the real jinja venv. Cause not investigated (no code
  changed; a possible factor is that the container user is root, which is untested). Not tuned, not re-run with changed inputs.

## NOT_RUN
- Nothing skipped. Not covered: `claim.frozen.json`-based provenance verification (GitHub API 403), so `run_fresh_env.sh` uses `claim.json` with the unverified flag.
