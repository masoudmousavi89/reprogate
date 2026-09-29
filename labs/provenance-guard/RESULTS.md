# Provenance guard: Linux sanity run (2026-09-29)

`python3.8 labs/provenance-guard/cases.py` on Linux, CPython 3.8.20. Predictions: the "after the change" list in `PREDICTIONS.md`.

| case | predicted after the change | actual | match |
|---|---|---|---|
| c00 | sufficient=True | True, 4 EXACT_QUOTE | yes |
| c01, c02, c03 | False, REJECTED/EMPTY_OR_TOO_SHORT | False, REJECTED/EMPTY_OR_TOO_SHORT | yes |
| c04 | message REJECTED/AMBIGUOUS, sufficient False | as predicted | yes |
| c05, c06 | False, REJECTED/MALFORMED | as predicted | yes |
| c07 | True | True | yes |
| c08 | claim hashes differ for different bodies | `claim_sha256_equal_for_different_bodies=False` | yes |
| c09 (real jinja#843) | 8 anchors EXACT_QUOTE, message and location_function AMBIGUOUS, sufficient True | SKIPPED: `labs/jinja-843/issue843.body.md` missing, because the raw issue body cannot be fetched here (GitHub API 403, F-010) | not run |
