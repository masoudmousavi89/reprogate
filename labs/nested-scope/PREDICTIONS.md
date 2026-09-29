# Nested scopes in the location rule (F-034, decision_056): predictions committed BEFORE the code change

Runner: `py -3.8 labs/nested-scope/cases.py` (pure calls to `classify_run`, nothing is executed).
Founder decision (2026-09-29, option 2 after F-033): a `<genexpr>`, `<listcomp>`, `<setcomp>`, `<dictcomp>` or `<lambda>` frame
that really sits inside the target function counts as part of that function for the `location` rule. Defined precisely, not a
wildcard for any nested frame: only those five code-object names; only a frame of class TARGET (already plausibility-checked);
only when the AST of the real source shows the lexical nesting (the supervisor writes `enclosing_function`, the nearest
lexically enclosing `def`/`async def`, and only when every candidate node on that line agrees); the frame's own `rel_path`
must still equal the claim file. Local named functions, class bodies, callbacks and forged frames get no credit. Only the
location comparison changes; `target_causal_frame` stays the innermost TARGET frame and a matching run gets the evidence reason
`LOCATION_VIA_NESTED_SCOPE`. The worker's own `enclosing_function` value is never trusted (the supervisor drops it and computes it).

## Baseline (code after F-033): predicted
The old matcher ignores `enclosing_function`, so with the innermost frame being the nested scope:
- n01, n02, n03: match False (LOCATION_MISMATCH). n04: False. n05: False. n06: False (FORGED_TARGET_FRAME). n07: False.
- n08 (claim names `<genexpr>` itself): True. n09: False. n10: False. n11 (message claim): True (message-driven) with
  LOCATION_MISMATCH in the reasons. n12: True.

## Predictions for the change
- n01, n02, n03: True with LOCATION_VIA_NESTED_SCOPE (and no LOCATION_MISMATCH).
- n04 False (enclosing function differs). n05 False (a named local function is not a nested scope, whatever the field says).
- n06 False (forged frame). n07 False (no enclosing_function). n08 True and WITHOUT LOCATION_VIA_NESTED_SCOPE (direct match).
- n09 False (file mismatch). n10 False (the innermost frame is `helper`). n11 True, LOCATION_MISMATCH gone, LOCATION_VIA_NESTED_SCOPE present.
- n12 True, unchanged.
- Supervisor (real source files in unit tests): a genexpr in a method gets `enclosing_function` = the method name; a list
  comprehension inside a lambda inside a function gets the function name; a genexpr at module level gets none; a value the
  worker put in `enclosing_function` is overwritten by the AST-derived one, and a non-nested frame never carries the key.
- Matching runs: all 14 F-033 synthetic cases keep their results; the existing 115 unit tests pass.
- Labs: jinja-843 6 of 6 rows unchanged; labs 2-9: the row that F-033 changed (sortedcontainers-eq oracle before) is expected to
  return to SYMPTOM_REPRODUCED and its oracle to PASS (its claim location `__eq__` and the KeyError raised in a generator
  expression nested in `__eq__`); the other rows unchanged. Any other change is recorded as observed, not tuned.

Not covered: Linux, Docker mode, nested scopes deeper than one comprehension level in real projects, decorators, class bodies.
