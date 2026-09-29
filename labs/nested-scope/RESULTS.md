# Nested scopes in the location rule: results (2026-09-29; predictions in PREDICTIONS.md, committed first as 294a5f5)

Windows 11, Python 3.8.10, host mode. Raw jinja evidence deleted (personal paths); labs 2-9 evidence lives outside the repository in
the work directory (earlier runs kept as `evidence-<lab>-pre-f034`).

| item | prediction | observed |
|---|---|---|
| baseline (code after F-033), 12 cases | n01-n07, n09, n10 False; n08, n11, n12 True | all 12 as predicted |
| after the change, 12 cases | n01-n03 True with LOCATION_VIA_NESTED_SCOPE; n04-n07, n09, n10 False; n08 True (direct); n11 True with the nested reason; n12 True | all 12 as predicted |
| supervisor, real source files | genexpr in a method -> method name; listcomp in lambda in a function -> the function; module-level genexpr and class-body comprehension -> none; worker-supplied value overwritten or dropped | as predicted (12 new tests in `tests/test_nested_scope.py` pass) |
| unit tests | existing pass | 127 tests OK (115 + 12 new), 11 skipped |
| jinja-843 | 6 of 6 rows unchanged | 6 of 6 rows unchanged |
| labs 2-9 | sortedcontainers-eq oracle back to SYMPTOM_REPRODUCED / PASS; other rows unchanged | as predicted: sortedcontainers-eq oracle PASS (run evidence: reasons `LOCATION_VIA_NESTED_SCOPE`, causal frame `<genexpr>` with `enclosing_function` `__eq__`, anchors_matched exception_type and location); the other 6 runnable labs unchanged; more-itertools-falsy not run (needs Python 3.12) |

All predictions held; no other behaviour changed. The claim and fixtures of sortedcontainers-eq were not edited. Limits: only the
9 labs and synthetic cases were checked; nested scopes deeper than one comprehension level in real projects, decorators and class
bodies are not covered; Linux and Docker mode were not run.
