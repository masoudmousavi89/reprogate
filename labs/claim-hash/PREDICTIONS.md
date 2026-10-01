# Claim hash check (F-042): predictions committed BEFORE the run and BEFORE the code change

Runner: `py -3.8 labs/claim-hash/cases.py` (pure calls to `provenance_state` on frozen claims, nothing is executed).

## The weakness (found by reading the code, 2026-10-01)

`claim-check` computes `claim_sha256` over the claim, the anchor verdicts and the issue body hash, but no later step
recomputes it. `provenance_state` only reads the stored flags `provenance_verified` and `provenance_sufficient`. So a
frozen claim edited after freezing, with the flags left in place, is accepted as VERIFIED, and `provenance_sufficient`
set by hand is believed. This contradicts the requirement that a claim is frozen and hashed before the first run.

## Change (decided by the maintainer's instruction to continue; two details are the AI's and are to be confirmed)

When `provenance_verified` is true, `provenance_state` recomputes `claim_hash(doc)` and compares it with
`claim_sha256`. A missing, non-string or different hash raises `ValueError` ("claim changed after freezing"). The
sufficiency is recomputed from the anchors instead of read from the stored flag (AI detail 1). Documents with
`provenance_verified` false keep their behaviour (UNVERIFIED_ALLOWED or ValueError). Fields outside the hash (for example
a free-text note) stay editable on purpose (AI detail 2: the hash covers what the verdict depends on, not every key).

Known limit, stated before the run: the hash is integrity, not authenticity. Whoever edits a claim and also recomputes
`claim_sha256` produces a document that passes. The evidence bundle hashes (`hashes.json`) and the before/after oracle
are the other checks.

## Predictions on the CURRENT code (baseline, weakness expected)
- h00 unmodified: VERIFIED.
- h01 claim message edited after freezing: VERIFIED (the gap).
- h02 anchor text edited: VERIFIED (the gap).
- h03 INFERRED anchor flipped to EXACT by hand: INSUFFICIENT (the stored flag is false and is read, not recomputed).
- h04 issue body hash edited: VERIFIED (the gap).
- h05 `provenance_sufficient` set to True by hand with only the exception type anchored: VERIFIED (the flag is believed).
- h06 `claim_sha256` removed: VERIFIED (the gap).
- h07 claim edited and hash recomputed: VERIFIED.
- h08 unverified, not allowed: ValueError.
- h09 unverified, allowed: UNVERIFIED_ALLOWED.
- h10 free-text note edited: VERIFIED.
- h11 `claim_sha256` of the wrong type: VERIFIED (the gap).

## Predictions for the change
- h00: VERIFIED.
- h01, h02, h04, h06, h11: ValueError.
- h03: ValueError (the hash covers the anchor verdicts, so the hand flip is caught before sufficiency is looked at).
- h05: INSUFFICIENT (the flag is recomputed from the anchors; the hash does not include the flag).
- h07: VERIFIED (the known limit).
- h08: ValueError, h09: UNVERIFIED_ALLOWED (unchanged).
- h10: VERIFIED (outside the hash on purpose).
- `evaluate()` on a tampered frozen claim raises `ValueError` before any run, and `run`, `oracle` and `verify` print
  `ERROR: ...` and exit with code 2 (existing handling of `ValueError`).
- Unit tests: the existing 152 pass (11 skipped); new tests in `tests/test_provenance.py` cover h01-h11 and one
  `evaluate()` case.
- jinja-843 lab (`run_lab001.ps1`): 6 of 6 rows unchanged, `provenance_sufficient` True (the lab freezes its claim fresh
  on every run, so no stale frozen file is affected).
- Older frozen claim files made before F-027 (different hash formula) are rejected; they were already regenerated
  (decision_051, no compatibility shim).

## Results (recorded after the run)
(to be filled in after the run)
