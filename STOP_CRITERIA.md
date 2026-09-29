# Stop / continue criteria (pre-registered 2026-09-29, before any benchmark run)

Decided by the maintainer before the first measurement. The numbers are judgement calls, not derived from a formula.
They are not changed after data is seen; a change needs a new dated section that states why, and results already
measured are reported against the version that was in force when they were measured.

Verdicts: **BUILD** (continue and invest), **KILL** (stop this direction), **INCONCLUSIVE** (see the rule below).

## Metrics

| id | metric | definition | role |
|---|---|---|---|
| M1 | false accept rate | known-bad reproducers (wrong reason, direct raise, forged output, adversarial) whose outcome on the affected commit is `SYMPTOM_REPRODUCED` or `SYMPTOM_REPRODUCED_FLAKY`, divided by all known-bad reproducers in the set. An oracle PASS is not required for a count. | decides |
| M2 | true accept rate | correct reproducers (confirmed by a human label) whose before/after oracle is PASS, divided by all correct reproducers in the set. A run that cannot be evaluated (`ENV_FAILURE` or any environment problem) counts as not accepted and stays in the denominator. | decides |
| M3 | agreement with human labels | agreement of the verdict with human labels on same-bug semantic alignment (req_018 protocol) | reported only, until two independent human reviewers exist; with maintainer-only labels it is a preliminary annotation |
| M4 | coverage | issues from the random sample (`labs/sample-2026-09/PROTOCOL.md`) whose body contains a Python traceback and that can be evaluated from the issue text (not `NOT_EVALUATED`), divided by all such issues | rescope trigger, never KILL |

## Thresholds

| metric | KILL | BUILD | between |
|---|---|---|---|
| M1 | >= 20 % | <= 1 per 30 (<= 3.34 %) | INCONCLUSIVE |
| M2 | < 50 % | >= 80 % | INCONCLUSIVE |
| M4 | - | - | below 25 %: rescope (start `wrong_output` support earlier) |

## Sample

- At least 30 known-bad reproducers from at least 10 different bugs, and at least 20 correct reproducers from at least
  10 different bugs. Below these minimums the verdict is INCONCLUSIVE whatever the rates are.
- Held-out set: at least half of the known-bad reproducers come from a source the code was not tuned against (for
  example reproducers written from the issue text alone and labelled afterwards), not from the fixtures and attacks
  used during development.
- Every set (reproducers, labels, expected outcomes) is frozen and committed before its first run.

## Combination rule

- **KILL** if M1 or M2 is in its KILL zone.
- **BUILD** only if M1 and M2 are both in their BUILD zone and the sample minimums are met.
- Otherwise **INCONCLUSIVE**: exactly one more round with a sample twice as large. If that round is INCONCLUSIVE again,
  no accuracy claim is made anywhere (README, application, talk); the project may continue, described as experimental.

## Time limit

A verdict is due by 2026-11-15 or after 20 new labs, whichever comes first.

## Public claims before a verdict

Until a BUILD verdict exists, no public text or application states an accuracy, precision or reliability figure; it
may describe the tool and its limits only.

## Change 2026-09-29: time limit

What changes: the verdict is due by **2026-10-13** or after 20 new labs, whichever comes first (was 2026-11-15). The
"one more round with a sample twice as large" of the combination rule moves to after the v0.1 alpha.

Why: the maintainer set a 14-day schedule to finish the v0.1 alpha.

What does not change: the metrics, their definitions, the thresholds, the sample minimums, the held-out rule, the
combination rule and the rule on public claims.

Disclosure: this change is made after data was seen. M4 was already measured (6 of 30 = 20 %, rescope; see
`labs/sample-v3/CHECKLIST-WIDE.md`) and the M1/M2 labelling had already stopped with 6 evaluable bugs, below the sample
minimum (see `labs/sample-v3/DEVIATIONS.md`). Only the date changes, so those results stand as measured. With the
current sample the M1/M2 verdict at the new date is expected to be INCONCLUSIVE.
