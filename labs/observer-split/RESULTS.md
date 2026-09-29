# Observer split / frame plausibility: Linux results (2026-09-29)

Predictions: the section "Linux verification run" in `PREDICTIONS.md`, committed in f64c0b3 before these runs
(the unit-test run of step 1 was the exception: it was executed once BEFORE that section was written).
Environment: Linux container, CPython 3.8.20 (uv), Docker 29.3.1, image `mirror.gcr.io/library/python:3.8-slim`
(cachetools has no dependencies). jinja image: same base plus `MarkupSafe==2.0.1` from a host-downloaded wheel, `--no-index` (F-018).
Provenance not verifiable here (GitHub API 403, F-010): `--allow-unverified-provenance`, qualifier `PROVENANCE_UNVERIFIED`.
Checkouts: cachetools `977e1c4^`, jinja `81825095` / `9a7dd7b2`, more-itertools `def2dab^` / `def2dab` (all under `<LAB>`).

| item | prediction | result | match |
|---|---|---|---|
| unit tests | Ran 100, OK, 0 skipped | `Ran 100 tests`, `OK`, 0 skipped: the 5 POSIX-only tests ran and the 6 Docker tests ran (Docker up, image present). Run before the prediction was committed. Windows: 100 OK / 11 skipped = 5 POSIX-only + 6 Docker | yes |
| b01 host / Docker | not SYMPTOM_REPRODUCED | NO_MATCHING_REPRODUCTION_FOUND / NO_MATCHING_REPRODUCTION_FOUND (5 COMPLETED; as in F-024, b01 fails on its own command-line lookup) | yes |
| b02 host / Docker | not SYMPTOM_REPRODUCED (FORGED_TARGET) | NO_MATCHING_REPRODUCTION_FOUND in both; the forged frame is `FORGED_TARGET`, `plausibility_note: not_a_target_file` | yes |
| b03 host / Docker | not SYMPTOM_REPRODUCED | INCONCLUSIVE / INSUFFICIENT_VALID_RUNS, 5 INVALID in both | yes |
| b04 host / Docker | not SYMPTOM_REPRODUCED; Docker fails earlier with ProcessLookupError | host: INCONCLUSIVE, 5 INVALID; Docker: NO_MATCHING_REPRODUCTION_FOUND, exception `ProcessLookupError` (kill path not exercised in Docker, as in F-024) | yes |
| b05 host / Docker | SYMPTOM_REPRODUCED | SYMPTOM_REPRODUCED, 5 of 5 matching, in both modes | yes |
| jinja-843, `run_lab001.sh`, host | 6 of 6 rows, qualifier PROVENANCE_UNVERIFIED | 6 of 6 rows YES (oracle PASS; unpinned ENVIRONMENT_UNAVAILABLE; f01 REJECTED; f02-f04 NO_MATCHING_REPRODUCTION_FOUND); all bundles carry `PROVENANCE_UNVERIFIED` | yes |
| more-itertools-falsy, Python 3.12, host | oracle PASS, f01 REJECTED, f02/f03 NO_MATCHING | oracle before SYMPTOM_REPRODUCED, after NO_MATCHING_REPRODUCTION_FOUND, post-fix CLEAN_COMPLETION, ORACLE PASS; f01 NOT_EVALUATED/REPRODUCER_REJECTED; f02, f03 NO_MATCHING_REPRODUCTION_FOUND | yes |
| honest TARGET frames | none becomes FORGED_TARGET | oracle before/after and all lab runs above kept their predicted outcomes, so no honest frame was rejected (frames were not counted one by one on Linux) | yes, weaker check than the Windows count |

Conclusion: the open F-026 predictions (b02 no longer reproduces, b05 still does, host and Docker) held on Linux.
Limits: not a security boundary, `observation_integrity` stays BEST_EFFORT_IN_PROCESS; b05 is accepted in both modes by design.
