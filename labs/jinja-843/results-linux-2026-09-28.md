# LAB-001 results: Linux run (2026-09-28)

Environment: Linux container, CPython 3.8.20 (uv), host runner (no sandbox).
Checkouts: `jinja-before` = 81825095d24f4dbccb40f787fff70db54989b91c (first parent of fix),
`jinja-after` = 9a7dd7b28b50fd8adc019ab2702b50ae5c6ed782. Pinned venv: MarkupSafe 2.0.1;
unpinned venv: MarkupSafe 2.1.5.

Unit tests: `python3.8 -m unittest discover -s tests -t .` -> Ran 43 tests, OK.

Provenance: the raw issue body could not be fetched (GitHub API HTTP 403), so all runs used
`--allow-unverified-provenance` (see F-010).

| case | expected | actual | ok |
|---|---|---|---|
| oracle | before=SYMPTOM_REPRODUCED post=CLEAN_COMPLETION pass=True | before=SYMPTOM_REPRODUCED post=CLEAN_COMPLETION pass=True | YES |
| case_c_unpinned | NOT_EVALUATED/ENVIRONMENT_UNAVAILABLE | NOT_EVALUATED/ENVIRONMENT_UNAVAILABLE | YES |
| f01_direct_raise | NOT_EVALUATED/REPRODUCER_REJECTED | NOT_EVALUATED/REPRODUCER_REJECTED | YES |
| f02_direct_deque_popleft | NO_MATCHING_REPRODUCTION_FOUND/NONE | NO_MATCHING_REPRODUCTION_FOUND/NONE | YES |
| f03_fake_traceback_stdout | NO_MATCHING_REPRODUCTION_FOUND/NONE | NO_MATCHING_REPRODUCTION_FOUND/NONE | YES |
| f04_subclass_override | NO_MATCHING_REPRODUCTION_FOUND/NONE | NO_MATCHING_REPRODUCTION_FOUND/NONE | YES |

`verify` on the oracle "before" bundle: hashes OK, same outcome, commit and environment match (PASS).
