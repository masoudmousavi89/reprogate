# Labs 6-9 results (Linux, host mode, provenance unverified; predictions committed in 4e0fcc2)

| lab | interpreter | oracle before | oracle after | oracle | fixtures f01/f02/f03 |
|---|---|---|---|---|---|
| sortedcontainers-eq (KeyError) | 3.8 | SYMPTOM_REPRODUCED | CLEAN_COMPLETION | PASS | as predicted |
| cachetools-27 (ValueError) | 3.8 | SYMPTOM_REPRODUCED | CLEAN_COMPLETION | PASS | as predicted |
| dateutil-981 (TypeError; needs `six`) | 3.8 | SYMPTOM_REPRODUCED | CLEAN_COMPLETION | PASS | as predicted |
| more-itertools-falsy (ValueError; fix needs Python >= 3.10) | 3.12 | SYMPTOM_REPRODUCED | CLEAN_COMPLETION | PASS | as predicted |

Selection bias: the bugs were picked by the author from fix commits with regression tests.
