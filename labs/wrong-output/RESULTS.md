# `wrong_output` version 1: results (2026-09-29; predictions in PREDICTIONS.md, committed first as c9ebfe4)

Windows 11, Python 3.8.10, host mode, synthetic library only. Status: EXPERIMENTAL; no claim about real bugs.

| item | prediction | observed |
|---|---|---|
| baseline (code before the change), 11 cases | w01, w07 NO_MATCHING with oracle FAIL; w02, w03, w05, w06, w10, w11 NO_MATCHING; w04 NOT_EVALUATED/REPRODUCER_REJECTED; w08, w09 match False; maturity absent | all 11 as predicted |
| after the change, 11 cases | w01, w07 SYMPTOM_REPRODUCED with oracle PASS; w02, w03, w05, w06 NO_MATCHING; w04 REPRODUCER_REJECTED; w10, w11 NOT_EVALUATED/CLAIM_UNSUPPORTED; w08 match False; w09 match True (known weakness) | all 11 as predicted; w08 reasons RETURNS_FROM_FORGED_FRAMES_IGNORED, NO_TARGET_RETURN_OBSERVED; w09 RETURN_EQUALS_ACTUAL |
| maturity | EXPERIMENTAL on wrong_output outcomes, STABLE_V0 on exception outcomes | as predicted (unit tests); w11 (kind `unexpected_exit`) has no maturity (null), as the schema allows |
| unit tests | the existing 141 pass | 152 tests OK (141 + 11 new in `tests/test_wrong_output.py`), 11 skipped |

All predictions held; no miss. w09 passes the forgery as predicted: a reproducer that re-implements the result protocol can
still forge a plausible return (residual weakness of F-026); the protocol was not adjusted to change that result.

Implementation notes (not predicted, recorded): the worker watches the target with `sys.settrace` (only frames of the claimed
file and function are traced); a reproducer that turns tracing off gets no recorded return and therefore no match (fails
closed). A return that follows an exception event with the value None is marked `raised` and not used. Only the main thread is
traced. Not covered: output files, printed output, timing, GUI, float tolerance, real bugs, Linux and Docker mode.
