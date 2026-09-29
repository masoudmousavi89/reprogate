# Labs 2-9 on Windows (Python 3.8.10, host mode, tool commit e0f692a, matcher of 8d26ea2)

Run with `tools/run_lab.py`; the raw issue body is fetched when the claim has an issue number. Predictions were
committed before the first runs of these labs (see F-014, F-019); nothing was changed.

| lab | claim provenance | rows matching the prediction |
|---|---|---|
| tabulate-180 | VERIFIED (both anchors EXACT_QUOTE) | 4 of 4 |
| more-itertools-707 | VERIFIED (both anchors EXACT_QUOTE) | 5 of 5 |
| cachetools-63 | UNVERIFIED: anchors `ValueError` and `value too large` are not in the issue body (INFERRED, not found) | 4 of 4 |
| tabulate-empty-cell | UNVERIFIED: claim has no issue number | 4 of 4 |
| cachetools-27 | UNVERIFIED: no issue number | 4 of 4 |
| sortedcontainers-eq | UNVERIFIED: no issue number | 4 of 4 |
| dateutil-981 | UNVERIFIED: no issue number (needs `six`, now `env.pip`) | 4 of 4 |
| more-itertools-falsy | not run: needs Python 3.12, only 3.8 on this machine | - |

Docker mode was not run here.
