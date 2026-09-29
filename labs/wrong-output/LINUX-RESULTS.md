# `wrong_output` version 1 (F-039): Linux validation results (2026-09-29)

Predictions: `LINUX-PREDICTIONS.md` (155ed40), committed before the run. Environment: Linux container (root), uv CPython 3.8.20, Docker 29.x,
image `mirror.gcr.io/library/python:3.8-slim`, unverified provenance flag where the CLI needs it. No code was changed. Status stays EXPERIMENTAL.

| item | prediction | observed |
|---|---|---|
| `labs/wrong-output/cases.py` (host mode) | the 11 lines of the "after the change" row of `RESULTS.md` | 11 lines as predicted: w01 and w07 `['SYMPTOM_REPRODUCED', 'NONE']` with oracle PASS; w02, w03, w05, w06 NO_MATCHING_REPRODUCTION_FOUND/NONE; w04 NOT_EVALUATED/REPRODUCER_REJECTED; w10 and w11 NOT_EVALUATED/CLAIM_UNSUPPORTED; w08 `match False` (RETURNS_FROM_FORGED_FRAMES_IGNORED, NO_TARGET_RETURN_OBSERVED); w09 `match True` (RETURN_EQUALS_ACTUAL). matches |
| full unit suite | 152 run, 0 failures, 0 errors, 0 skipped | 152 run, OK, 0 skipped after Docker was running. A first run, made while the Docker daemon was not up (stale `docker.pid` and socket left from the container restart), gave `OK (skipped=6)`: the 6 Docker tests skipped. That was an environment problem, not a test result; after removing the stale files and restarting the daemon the suite gave `Ran 152 tests`, `OK`, 0 skipped. matches |
| Docker oracle, w01 | before SYMPTOM_REPRODUCED, after-fix CLEAN_COMPLETION, ORACLE PASS; run 1 "before" observation holds exactly one return, value `200`, frame class TARGET | `before: SYMPTOM_REPRODUCED/NONE | after: NO_MATCHING_REPRODUCTION_FOUND/NONE | post-fix: CLEAN_COMPLETION`, ORACLE PASS, sandbox kind DOCKER (3 runs, min 3 completed); run 1 `returns` has 1 entry: `value_repr` `200`, frame class TARGET (`shoplib/money.py`, function `change`, path `/repo/...` inside the container). matches |

## Misses
None.

Operator note: the Docker daemon needed a restart before the suite could exercise the Docker tests (see item 2); the helper used for the Docker oracle was kept outside the repository and deleted.
