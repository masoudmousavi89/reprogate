# `wrong_output` claims, version 1 (EXPERIMENTAL): design, fixed before the code

Status: EXPERIMENTAL. No accuracy or usefulness claim is made for this claim kind. Maintainer decision, 2026-09-29, after
the M4 rescope (`labs/sample-v3/CHECKLIST-WIDE.md`).

## What a claim says

A bug where the code runs but returns a wrong value. The claim has four parts, all taken from the issue text:

```json
{"kind": "wrong_output",
 "target": {"file": "pkg/module.py", "function": "name"},
 "input": "text of the call or input as the issue states it",
 "expected": "300",
 "actual": "200"}
```

- `expected` and `actual` are Python literals as text (numbers, strings, booleans, None, and lists / tuples / dicts / sets of
  those), parsed with `ast.literal_eval`. If either is missing or not a literal, or the input is not stated, the claim is
  UNSUPPORTED: outcome NOT_EVALUATED, reason CLAIM_UNSUPPORTED.
- Anchors for provenance: the target function name, `expected` and `actual` as they appear in the issue.

## What is observed (never the reproducer's own output)

- The worker records every return of the target function: a frame whose code name is `target.function` and whose file is
  `target.file` inside the repository. For each return it records `repr()` of the returned value at the moment of return
  (bounded length) and `repr()` of the arguments (evidence only, not used by the verdict).
- The supervisor reclassifies the frame as today (`TARGET` only when the path is authentic; forged frames are
  `FORGED_TARGET`) and keeps only returns from authentic `TARGET` frames.
- stdout and stderr are never used, as for exception claims.

## Verdict

- Per run: symptom match if at least one kept return equals `actual` (`ast.literal_eval` of the recorded repr compared with
  `ast.literal_eval` of `actual`; if the repr is not a literal, the texts are compared). An exception does not match a
  `wrong_output` claim.
- Expected behaviour (after the fix): no kept return equals `actual` and at least one equals `expected`.
- Oracle: before the fix SYMPTOM_REPRODUCED (or FLAKY) and after the fix every completed run shows the expected behaviour
  => PASS. The project's fix is the reference for the expected value; no human label is needed.
- Every outcome records `claim_kind` and `claim_kind_maturity` (`EXPERIMENTAL` for `wrong_output`, `STABLE_V0` for
  `exception`). This is a separate field because `outcome_qualifier` holds one value and is already used for unverified
  provenance.
- Claim kinds other than `exception` and `wrong_output` (for example `unexpected_exit`) become UNSUPPORTED. Today the tool
  does not check the kind at all and silently treats every claim as an exception claim.

## Unchanged

The static gate (monkeypatching or replacing target code is rejected), the observer split, frame plausibility, fresh
environments, invariants, bundle checks and all behaviour for exception claims.

## Known limits (stated before the code)

- A reproducer that re-implements the supervisor's result protocol can still forge an observation, now including a return
  (the residual weakness of F-026). Case w09 checks exactly this and is expected to pass the forgery; it measures version 1,
  and the protocol will not be adjusted afterwards to change that result.
- The call's input is recorded but not checked against the claim; the before/after oracle is what rules out a lucky input.
- Exact equality only (no float tolerance); a value mutated after it was returned is judged by its repr at return time.
- Not covered: output files, printed output, timing, GUI, real bugs (a separate protocol later).
