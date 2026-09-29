# Predictions for the F-020 changes (written and committed BEFORE the code change)

Changes: (1) when the claim has a message, the message must be contained in the exception message to match
(location alone no longer suffices); (2) bundles of a plain `run` with SYMPTOM_REPRODUCED* carry
`oracle_required: true`; bundles inside an `oracle` do not.

Predicted after the change:
- attack a10 (look-alike message): NO_MATCHING_REPRODUCTION_FOUND (was SYMPTOM_REPRODUCED).
- attack a04 (builtin callable crafts a message that contains the claim text): still SYMPTOM_REPRODUCED, oracle still FAIL.
- attacks a01-a03, a05-a09: unchanged.
- all rows of labs jinja-843, tabulate-180, tabulate-empty-cell, cachetools-63, more-itertools-707,
  sortedcontainers-eq, cachetools-27, dateutil-981, more-itertools-falsy: unchanged (host mode and Docker).
- unit tests: the existing ones still pass; new tests cover the message rule and the flag.
