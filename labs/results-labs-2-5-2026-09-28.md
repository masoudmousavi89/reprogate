# Labs 2-5 results (Linux, CPython 3.8.20, host runner, provenance unverified)

Predictions were committed in 2addf33 before this run.

| lab | oracle before | oracle after | oracle | gamed fixtures f01/f02/f03 |
|---|---|---|---|---|
| tabulate-180 (IndexError) | SYMPTOM_REPRODUCED | CLEAN_COMPLETION | PASS | as predicted |
| tabulate-empty-cell (TypeError) | SYMPTOM_REPRODUCED | CLEAN_COMPLETION | PASS | as predicted |
| cachetools-63 (ValueError) | SYMPTOM_REPRODUCED | CLEAN_COMPLETION | PASS | as predicted |
| more-itertools-707 (RuntimeError) | NOT_EVALUATED/REPRODUCER_REJECTED | same | FAIL (predicted PASS) | as predicted |

The failure is a finding (F-011, F-012), not hidden. A variant without a raise statement was also tried
(`labs/more-itertools-707/repro_no_raise_stmt.py`): the gate accepts it but the outcome is
NO_MATCHING_REPRODUCTION_FOUND because the exception has no target frame.
