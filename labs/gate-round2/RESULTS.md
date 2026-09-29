# Gate round 2: results (2026-09-29; predictions in PREDICTIONS.md, committed before the run)

Target: labs/cachetools-63, Docker sandbox (python:3.8-slim); a06 in host mode on a throwaway copy.

| attack | gate | outcome | as predicted |
|---|---|---|---|
| a01 hidden exec/compile, forged filename | VALID | NO_MATCHING_REPRODUCTION_FOUND | yes |
| a02 same, real module globals | VALID | NO_MATCHING_REPRODUCTION_FOUND | yes |
| a03 catch library error, then raise look-alike | VALID | NO_MATCHING_REPRODUCTION_FOUND | yes |
| a04 builtin `int` as getsizeof crafts the message | VALID | SYMPTOM_REPRODUCED (5/5) | yes (false positive predicted); oracle FAIL (after-fix STILL_FAILS) |
| a05 real trigger in half of the runs | VALID | SYMPTOM_REPRODUCED_FLAKY | yes |
| a06 tamper with a repository file | VALID | INCONCLUSIVE / REPOSITORY_MODIFIED (5 invalid runs) | yes |
| a07 memory bomb | VALID | INCONCLUSIVE / INSUFFICIENT_VALID_RUNS (5 invalid) | yes |
| a08 100 MB stdout | VALID | NO_MATCHING_REPRODUCTION_FOUND, bundle 496 KB | yes |
| a09 exit(1) + claim text on stderr | VALID | NO_MATCHING_REPRODUCTION_FOUND | yes |
| a10 a04 with a look-alike character in the message | VALID | SYMPTOM_REPRODUCED (5/5) | **no** (predicted NO_MATCH) |

Reading: no attack got a clean SYMPTOM_REPRODUCED from a bundle that also passes the oracle. The gate itself let all
ten through (it is a first line, not a boundary); the matcher, the tree hash and the container did the work.
The miss (a10) exposes that the match rule is `type AND (message OR location)`: a ValueError raised inside
`__setitem__` matches the claim by location even when the message differs, so the message anchor is weak.
a04/a10 need no library defect at all (a user-supplied builtin callable fails), so a single run cannot separate
them from a real bug; only the before/after oracle does (F-015 rule).
