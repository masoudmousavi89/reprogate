# `wrong_output` version 1: predictions committed BEFORE the code and BEFORE the run

Runner: `py -3.8 labs/wrong-output/cases.py`. Design: `DESIGN.md`. Synthetic library `shoplib`: `change(paid, price)` returns
`paid - price - 100` before the fix and `paid - price` after it; `buy()` calls `change()`; a price above the payment raises
`ValueError` in both versions. Claim: target `shoplib/money.py:change`, input `change(1000, 700)`, expected `300`, actual `200`.
Part A runs 3 host-mode runs per case with our own scripts only (unverified provenance allowed); part B calls the matcher
directly.

## Baseline (current code): predicted

The current code does not check the claim kind; a `wrong_output` claim is judged as an exception claim with no exception
type, so it can never match.

| case | predicted |
|---|---|
| w01 correct reproducer | NO_MATCHING_REPRODUCTION_FOUND/NONE; oracle FAIL |
| w02 prints 200 only | NO_MATCHING_REPRODUCTION_FOUND/NONE |
| w03 own function returning 200 | NO_MATCHING_REPRODUCTION_FOUND/NONE |
| w04 replaces the target function | NOT_EVALUATED/REPRODUCER_REJECTED (gate: PATCHES_TARGET) |
| w05 other input (returns 100) | NO_MATCHING_REPRODUCTION_FOUND/NONE |
| w06 target raises ValueError | NO_MATCHING_REPRODUCTION_FOUND/NONE |
| w07 indirect call through buy() | NO_MATCHING_REPRODUCTION_FOUND/NONE; oracle FAIL |
| w10 non-literal expected | NO_MATCHING_REPRODUCTION_FOUND/NONE |
| w11 claim kind unexpected_exit | NO_MATCHING_REPRODUCTION_FOUND/NONE |
| w08 forged frame (part B) | match False (NO_EXCEPTION_OBSERVED) |
| w09 protocol forgery (part B) | match False (NO_EXCEPTION_OBSERVED) |

`claim_kind_maturity` is absent (printed as None) everywhere in the baseline. No crash is predicted.

## Predictions for the change

| case | predicted |
|---|---|
| w01 | SYMPTOM_REPRODUCED/NONE; oracle PASS; maturity EXPERIMENTAL |
| w02 | NO_MATCHING_REPRODUCTION_FOUND/NONE (no return of the target observed) |
| w03 | NO_MATCHING_REPRODUCTION_FOUND/NONE (the function is not the target) |
| w04 | NOT_EVALUATED/REPRODUCER_REJECTED (gate, unchanged) |
| w05 | NO_MATCHING_REPRODUCTION_FOUND/NONE (the target returned 100, not 200) |
| w06 | NO_MATCHING_REPRODUCTION_FOUND/NONE (an exception does not match a wrong_output claim) |
| w07 | SYMPTOM_REPRODUCED/NONE; oracle PASS (the target is called by the library itself) |
| w10 | NOT_EVALUATED/CLAIM_UNSUPPORTED (expected is not a literal) |
| w11 | NOT_EVALUATED/CLAIM_UNSUPPORTED (kind not supported) |
| w08 | match False (a return from a FORGED_TARGET frame is not kept) |
| w09 | **match True: the known residual weakness of F-026.** A reproducer that re-implements the result protocol can forge a plausible return. This case measures version 1; the protocol is not adjusted afterwards to change this result. |

- Maturity is `EXPERIMENTAL` on every `wrong_output` outcome (part A, w01-w07) and `STABLE_V0` on exception outcomes.
- Unit tests: the existing 141 pass; exception-claim behaviour is unchanged.
- The finding (F-039) is written only with the code and the results.

Not covered: output files, printed output, timing, GUI, float tolerance, real bugs, Linux (run later), Docker mode.
