# LAB-001 on Windows with the supervisor/worker harness (2026-09-29, output relayed by the maintainer)

Commit 0bc3776, `py -3.8`. Unit tests: 68 run, OK, 10 skipped (6 Docker, 4 POSIX-only forgery tests).
Claim-check: `provenance_sufficient: True`.

| case | expected | actual | ok |
|---|---|---|---|
| oracle | before=SYMPTOM_REPRODUCED post=CLEAN_COMPLETION pass=True | same | YES |
| case_c_unpinned | NOT_EVALUATED/ENVIRONMENT_UNAVAILABLE | same | YES |
| f01_direct_raise | NOT_EVALUATED/REPRODUCER_REJECTED | same | YES |
| f02_direct_deque_popleft | NO_MATCHING_REPRODUCTION_FOUND/NONE | same | YES |
| f03_fake_traceback_stdout | NO_MATCHING_REPRODUCTION_FOUND/NONE | same | YES |
| f04_subclass_override | NO_MATCHING_REPRODUCTION_FOUND/NONE | same | YES |

Timeout check: `while True: pass`, `--timeout 5`, 5 runs: all TIMEOUT, outcome INCONCLUSIVE / TIMEOUT_NOT_CLAIMED,
no leftover harness or worker process.
