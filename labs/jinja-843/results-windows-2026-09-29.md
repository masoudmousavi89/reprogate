# LAB-001 results: Windows run (2026-09-29, output pasted by the maintainer)

Interpreter: `py -3.8`. Unit tests: Ran 52 tests, OK (27.6 s).

Provenance: raw issue body fetched from the GitHub API (updated_at 2020-11-13T20:15:26Z, state closed).
claim-check: exception_type, message, location_file, location_function, trigger_1..4 all EXACT_QUOTE;
`provenance_sufficient: True`. Bundles carry no PROVENANCE_UNVERIFIED qualifier.

| case | expected | actual | ok |
|---|---|---|---|
| oracle | before=SYMPTOM_REPRODUCED post=CLEAN_COMPLETION pass=True | same | YES |
| case_c_unpinned | NOT_EVALUATED/ENVIRONMENT_UNAVAILABLE | same | YES |
| f01_direct_raise | NOT_EVALUATED/REPRODUCER_REJECTED | same | YES |
| f02_direct_deque_popleft | NO_MATCHING_REPRODUCTION_FOUND/NONE | same | YES |
| f03_fake_traceback_stdout | NO_MATCHING_REPRODUCTION_FOUND/NONE | same | YES |
| f04_subclass_override | NO_MATCHING_REPRODUCTION_FOUND/NONE | same | YES |
