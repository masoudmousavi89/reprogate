# Architecture (prototype 0.1-proto, schema unstable)

```
claim.json --claim-check(raw issue body)--> claim.frozen.json   (anchors EXACT_QUOTE or INFERRED, hashed)
reproducer --gate (AST, never executed)---> VALID | REJECTED | UNSAFE | NOT_AUDITABLE
                 |
                 v (VALID only)
   N x fresh process:  <target python> harness.py --repo <checkout> --repro repro.py
                 |         harness = same interpreter as the reproducer (BEST_EFFORT_IN_PROCESS)
                 v
   observation.json (exception type/message, frames classified TARGET / FORGED_TARGET / REPRODUCER /
                     STDLIB / THIRDPARTY, phase import|trigger, exit code)     stdout/stderr = diagnostics only
                 |
   repo tree hash before/after every run  -> REPOSITORY_MODIFIED
                 |
   matcher (per run) -> aggregate (per bundle) -> outcome + outcome_reason -> evidence bundle + hashes.json
```

## Matching rules (0.x, heuristic)

- Origin: >= 1 authentic TARGET frame, no FORGED_TARGET frame, and no REPRODUCER frame after the first
  TARGET frame. A frame is *authentic* only if its globals are the real module's `__dict__`, the module file
  equals the frame file, and the running bytecode equals a fresh compile of that file.
  (This catches direct raises, callbacks, overrides and `compile(..., fake_filename)` tricks.)
- Exception (F-012): a PEP 479 conversion (`RuntimeError: generator raised StopIteration` and its coroutine /
  async siblings, closed whitelist) has no target frame of its own; origin is then taken from its explicit
  `__cause__`, which must have the expected type and an authentic TARGET frame, and the primary exception must
  not have been raised by a `raise` line of the reproducer.
- Gate (F-011): `raise` is allowed only inside a function body (callback triggers); module level, class
  body and `except` handlers stay rejected.
- Match = origin ok AND exception type equal AND (message contained OR location file+function matches).
  Exception type alone never matches. Line numbers are never used.
- Import-phase `ImportError` / `ModuleNotFoundError` / `SyntaxError` that is not the claimed symptom is
  `ENV_FAILURE`, never "no reproduction".

## Aggregation (default 5 runs, min 3 valid; thresholds are heuristics, tune after the benchmark)

`ENV_FAILURE` and `TIMEOUT` runs are excluded from the matching denominator but recorded.
all match -> `SYMPTOM_REPRODUCED`; 2..n-1 -> `..._FLAKY`; exactly 1 -> `INCONCLUSIVE/SINGLE_MATCH_ONLY`;
0 -> `NO_MATCHING_REPRODUCTION_FOUND`; all env failures -> `NOT_EVALUATED/ENVIRONMENT_UNAVAILABLE`.
Reasons added beyond the design file's first list: `SINGLE_MATCH_ONLY`, `TIMEOUT_NOT_CLAIMED`,
`REPOSITORY_MODIFIED`, `CLAIM_PROVENANCE_INSUFFICIENT`.

## Oracle

`oracle` = same reproducer, before-fix must be `SYMPTOM_REPRODUCED` AND after-fix must be a **clean
completion in every run** (exit 0, no exception). "No longer matches" is not enough. Fail-to-pass is a
necessary helper, not ground truth.

## Evidence fields present from day one

`reproducer_origin`, `attempts_before_submission`, `claim_faithfulness` (NOT_REVIEWED),
`observation_integrity`, `environment_trust`, `sandbox`, `claim_provenance`, `outcome_qualifier`.
