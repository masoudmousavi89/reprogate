# Provenance guard (F-027): predictions committed BEFORE the run and BEFORE the code change

Runner: `py -3.8 labs/provenance-guard/cases.py` (pure calls to `check_claim`, nothing is executed).
Decisions (founder, 2026-09-29): minimum anchor length 3 characters (conservative guard, not a semantic claim);
an anchor that occurs more than once in the raw body is rejected; `claim_hash` must bind the real issue snapshot and
dependent frozen artifacts are regenerated, no artificial compatibility. One addition by the AI, to be confirmed:
the length guard counts the text after `strip()`, so an anchor made of whitespace only is also too short.

## Predictions on the CURRENT code (baseline, weakness expected)
- c00 four good anchors: sufficient=True.
- c01 empty anchors: EXACT_QUOTE at 0-0 for both, sufficient=True (the bug).
- c02 one and two character anchors: EXACT_QUOTE, sufficient=True.
- c03 whitespace-only anchors: EXACT_QUOTE, sufficient=True.
- c04 message `Box` (occurs twice): EXACT_QUOTE, sufficient=True.
- c05 anchor without `text`: crashes with KeyError.
- c06 anchor with non-string `text`: crashes with AttributeError or TypeError.
- c07 `Err` (3 chars, once) plus the file anchor: sufficient=True.
- c08 same-length bodies with different content: claim_sha256 equal (True).
- c09 real jinja#843: all 8 anchors EXACT_QUOTE, sufficient=True.

## Predictions for the change
New anchor states: EXACT (exactly one occurrence, stripped length >= 3), INFERRED (not found), REJECTED with a
closed `reject_reason`: EMPTY_OR_TOO_SHORT, AMBIGUOUS, MALFORMED. `provenance_sufficient` counts EXACT anchors only.
`claim_hash` includes `issue.body_sha256` and `reject_reason`.
- c00: unchanged, sufficient=True.
- c01, c02, c03: every anchor REJECTED/EMPTY_OR_TOO_SHORT, sufficient=False.
- c04: message REJECTED/AMBIGUOUS, sufficient=False (no location anchor to compensate).
- c05, c06: no exception; the bad anchor is REJECTED/MALFORMED; sufficient=False.
- c07: `Err` EXACT, sufficient=True (3 is allowed).
- c08: claim_sha256 differs (equal = False).
- c09 real jinja#843: `message` and `location_function` occur twice in the raw body, so they become REJECTED/AMBIGUOUS;
  the other 6 stay EXACT; sufficient stays True (exception_type + location_file). This changes what the frozen claim
  says about the message anchor, and the matcher still uses the claim's message (it does not read provenance).
- jinja-843 lab (`run_lab001.ps1`): 6 of 6 rows unchanged, provenance_sufficient True, claim_sha256 differs from
  the earlier frozen claim (it is regenerated, the file is gitignored).
- unit tests: the existing ones pass; a new `tests/test_provenance.py` covers c00-c08.
- other labs (2-9): their claims are not frozen against a raw body in the repository; not re-run here except
  tabulate#180 and more-itertools#707, whose bodies are fetched to check claim-check (prediction: unknown, may
  lose anchors that occur twice; that is recorded as observed, not tuned).

## Results (recorded after the run)
Baseline (before the code change): all 10 predictions held, including c01 (empty anchors, sufficient=True) and
c05/c06 (KeyError / AttributeError). After the change: all predictions held (c00 True, c01-c06 False with the
predicted reasons, c07 True, c08 hashes differ, c09 message and location_function AMBIGUOUS, sufficient True).
91 unit tests OK (12 new), 11 skipped (5 POSIX-only, 6 Docker). jinja-843 lab: 6 of 6 rows unchanged.
Unpredicted-in-detail (the prediction said "unknown"): tabulate#180 unchanged (2 of 2 EXACT); more-itertools#707
`exception_type` `RuntimeError` occurs twice, so `provenance_sufficient` is now False. Recorded, not tuned (F-027).
