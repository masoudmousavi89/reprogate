# Matcher rules: results (2026-09-29; predictions in PREDICTIONS.md, committed first as 22b14cb)

Windows 11, Python 3.8.10, host mode. Raw evidence folders of the jinja run deleted (personal paths); the labs 2-9 evidence
lives outside the repository in the work directory (old runs kept as `evidence-<lab>-pre-f033`).

| item | prediction | observed |
|---|---|---|
| baseline (old code), 14 synthetic cases | m01-m14 as listed, origin/causal columns '-' | all 14 as predicted |
| after the change, 14 cases | as listed (A: m03, m09 False; C: m05 True, m06 False; m02 gains LOCATION_MISMATCH; origin/causal recorded) | all 14 as predicted |
| unit tests | existing pass, new file covers m01-m14 | 115 tests OK (107 + 8 new in `tests/test_matcher.py`), 11 skipped |
| jinja-843 | 6 of 6 rows unchanged | 6 of 6 rows unchanged; `anchors_verified` = exception_type, location_file, trigger_1-4; `anchors_not_verified` = message and location_function (AMBIGUOUS); run evidence has origin = causal = `TARGET __setitem__` (the raise is native, so no stdlib frame follows) |
| labs 2-9 | every row unchanged | 6 of 7 runnable labs unchanged (tabulate-180, more-itertools-707, cachetools-63, tabulate-empty-cell, cachetools-27, dateutil-981); **sortedcontainers-eq: the oracle row changed** (before: NO_MATCHING_REPRODUCTION_FOUND, expected SYMPTOM_REPRODUCED, oracle FAIL); more-itertools-falsy not run (needs Python 3.12) |

The changed row is a direct consequence of decision A and is recorded as observed, not tuned. Claim: KeyError, no message, location
`sortedcontainers/sorteddict.py::__eq__`. Real traceback frames: `__eq__` (TARGET, index 5) then `<genexpr>` (TARGET, index 6). The
innermost TARGET frame is the generator expression nested in `__eq__`, so the location `__eq__` no longer matches (reason
LOCATION_MISMATCH, `anchors_matched` only exception_type); the old code matched because `__eq__` was one of the target frames.
So a claim that names the enclosing function fails whenever the raise happens inside a comprehension, generator expression or
lambda of that function.

Side note (not caused by F-033): more-itertools-707 now runs with provenance UNVERIFIED, tabulate-180 stays VERIFIED. That is the
known consequence of F-027 (its `RuntimeError` anchor occurs twice in the raw issue body), already an open question.

Not covered: Linux, Docker mode, click-942 (sample protocol: a new run only with a new prediction), fastf1/taurus/httpie (not
evaluable), more-itertools-falsy.
