# `wrong_output` version 1 (F-039): Linux validation, predictions committed BEFORE the run

Second environment for F-039 (Windows results: `RESULTS.md`, 586c321). Linux container, uv CPython 3.8, Docker, image
`mirror.gcr.io/library/python:3.8-slim`. The Windows code is changed only if this run shows a failure or new evidence.

| item | prediction |
|---|---|
| `python3.8 labs/wrong-output/cases.py` (host mode) | the same 11 lines as the "after the change" row of `RESULTS.md`: w01 and w07 SYMPTOM_REPRODUCED with oracle PASS; w02, w03, w05, w06 NO_MATCHING; w04 NOT_EVALUATED/REPRODUCER_REJECTED; w10 and w11 NOT_EVALUATED/CLAIM_UNSUPPORTED; w08 match False; w09 match True |
| full unit suite | 152 run, 0 failures, 0 errors, 0 skipped (POSIX and Docker tests run here) |
| Docker oracle, w01 (new check, not run on Windows) | before SYMPTOM_REPRODUCED, after-fix classification CLEAN_COMPLETION, ORACLE PASS; the "before" observation of run 1 holds exactly one return, value `200`, frame class TARGET |

Status stays EXPERIMENTAL whatever the result; no accuracy or real-bug claim follows from this run.
