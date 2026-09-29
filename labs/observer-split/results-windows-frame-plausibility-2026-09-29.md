# Frame plausibility check (F-026) on Windows (Python 3.8.10, host mode)

Predictions were committed first (6fac072, deviation note ceae7dc). Labs run with `tools/run_lab.py`; earlier
evidence folders were kept aside, not overwritten.

| lab | claim provenance | rows matching the prediction |
|---|---|---|
| tabulate-180 | VERIFIED | 4 of 4 |
| more-itertools-707 | VERIFIED | 5 of 5 |
| cachetools-63 | UNVERIFIED | 4 of 4 |
| tabulate-empty-cell | UNVERIFIED | 4 of 4 |
| cachetools-27 | UNVERIFIED | 4 of 4 |
| sortedcontainers-eq | UNVERIFIED | 4 of 4 |
| dateutil-981 | UNVERIFIED | 4 of 4 |

Across the 145 observation files of these runs, 100 TARGET frames were checked and all got `plausibility_note: ok`;
no honest frame was marked FORGED_TARGET.

Unit tests: 79 run, 0 failures, 11 skipped (6 Docker, 5 POSIX-only).

Not run here: jinja-843 and more-itertools-falsy (needs Python 3.12), Docker mode, and the attacks b02 and b05
(they need `/proc/self/cmdline`, Linux only). Their predictions stay open until a Linux run.
