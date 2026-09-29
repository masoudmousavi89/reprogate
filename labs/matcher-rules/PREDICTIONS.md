# Matcher rules (F-033, req_009): predictions committed BEFORE the code change

Runner: `py -3.8 labs/matcher-rules/cases.py` (pure calls to `classify_run`, nothing is executed).
Founder decisions (2026-09-29): (A) `location` is compared only with the INNERMOST target frame (highest frame index among
TARGET frames), not with any target frame; (B) `anchors_verified` (which claim fields have an EXACT_QUOTE anchor) is evidence
only and does not change the verdict; the provenance gate in the matcher is a separate later decision; (C) a claim message
shorter than 3 characters (after strip) counts as no message for the matcher, so the message is not matched and exception
type plus location remain the criterion. `exception_origin` (innermost frame of the whole stack) and `target_causal_frame`
(innermost TARGET frame, or the innermost cause TARGET frame for an accepted interpreter conversion) are recorded as evidence
only and are not used by the verdict, except that (A) itself changes the location comparison.

## Baseline (current code): predicted
- m01 match True. m02 True (message-driven), reasons contain nothing about location. m03 True (location matched on an outer
  target frame). m04 True. m05 False (MESSAGE_MISMATCH: "e" is not in "boom"). m06 True ("ab" is in the message; the claim
  has no location, message decides). m07 True. m08 True. m09 True. m10 False (FORGED_TARGET_FRAME). m11 False
  (REPRODUCER_FRAME_AFTER_TARGET). m12 False. m13 True (ORIGIN_FROM_INTERPRETER_CONVERSION). m14 False (NO_EXCEPTION_OBSERVED).
- exception_origin and target_causal_frame columns are '-' (the fields do not exist).

## Predictions for the change
- m01 True. m02 True, plus reason LOCATION_MISMATCH (the outer frame no longer counts; the verdict stays message-driven).
- m03 False with LOCATION_MISMATCH (the only behaviour change caused by A on a message-less claim). m04 True.
- m05 True with reason MESSAGE_TOO_SHORT_IGNORED (consequence of C: a one-character message no longer blocks; location decides).
- m06 False (message ignored, the claim has no location, so no anchor remains). m07 True (3 characters is enough).
- m08 True; origin is the STDLIB frame, causal frame is the TARGET frame. m09 True? NO: m09 is message-less and its innermost
  TARGET frame is `_helper`, so LOCATION_MISMATCH and False; origin `STDLIB#3:popleft`, causal `TARGET#2:_helper`.
- m10, m11, m12, m14 unchanged (False). m13 True; causal frame is the innermost cause TARGET frame `TARGET#1:gen`.
- `exception_origin` / `target_causal_frame` are `None` for m14 and for runs without an exception; origin exists for every
  run with a traceback; causal frame is `None` when no TARGET frame exists.
- Labs: every lab row in `expected_outcomes.json` is unchanged (jinja-843 6 of 6, labs 2-9 as in F-019/F-022 on Windows).
  A changed row is recorded as observed, not tuned. Run reasons may gain LOCATION_MISMATCH on matching runs where only an outer
  frame carried the location (verdict unchanged).
- `outcome.json` gains `anchors_verified` (fields with an EXACT_QUOTE anchor) and `anchors_not_verified` (field -> state); the
  invariants validator ignores them (no invariant added). The jinja claim records `message` and `location_function` as not
  verified (REJECTED/AMBIGUOUS after F-027) while the matcher still uses them (decision B).
- Unit tests: existing pass; new `tests/test_matcher.py` covers m01-m14 plus the evidence fields.

Not covered: Linux runs, Docker mode, claims whose location anchor points at a frame that is not the innermost target frame in
the real issue tracebacks (only the 9 labs are checked).
