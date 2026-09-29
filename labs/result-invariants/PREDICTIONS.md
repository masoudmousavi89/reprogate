# Result invariants (F-029, req_003): predictions committed BEFORE the code and BEFORE the run

Runner: `py -3.8 labs/result-invariants/cases.py` (pure calls, nothing is executed).
Founder decisions (2026-09-29): `schema/result.schema.json` documents the contract only and the runtime validator is
stdlib only (no `jsonschema`); `verify` is fail-closed (invalid invariants => warning + non-zero exit code); older bundles
that violate the new invariants are reported invalid, no compatibility shim; `claim_status` is not touched (it stays
`READY` in the pipeline; a Claim Extractor is a real dependency).

The validator is `validate_outcome(outcome_dict) -> list of "CODE: message"`. Codes: MISSING_FIELD, ENUM, COUNTS_TOTAL,
COUNTS_TALLY, COUNTS_ORDER, REASON_OUTCOME, GATE_LINK, CLAIM_LINK, ENV_LINK, RUN_LINK, PROVENANCE, QUALIFIER, ORACLE.

## Baseline (before the validator exists)
`cases.py` prints `NO_VALIDATOR` for all 31 cases (there is no invariant check anywhere; `inspect` and `verify` only check
file hashes). Recorded as observed.

## Predictions for the change
- v01-v15 (15 valid outcomes produced by the real `aggregate()` over every branch: all match, flaky, single match, no
  match, match plus env failures, all env failure, too few valid runs, timeouts only, repository modified, gate rejected,
  provenance insufficient, unverified provenance allowed, harness error, claim UNSUPPORTED, and `oracle_required=false`
  inside an oracle): every one VALID, 0 false rejects.
- i01-i16 (16 impossible mutations): every one INVALID, 0 false accepts, with these primary codes:
  i01 REASON_OUTCOME; i02 REASON_OUTCOME; i03 REASON_OUTCOME; i04 COUNTS_ORDER; i05 COUNTS_ORDER; i06 COUNTS_ORDER;
  i07 COUNTS_TOTAL; i08 COUNTS_TALLY; i09 ENV_LINK; i10 PROVENANCE; i11 QUALIFIER; i12 GATE_LINK; i13 ENUM;
  i14 MISSING_FIELD; i15 ORACLE; i16 COUNTS_ORDER (a reproduction needs at least 2 matching runs).
  A case may show additional codes; only a missing primary code counts as a miss.
- The Lab #1 runner (`run_lab001.ps1`): 8 bundles (oracle before/after plus 5 runs), all pass the validator; 6 of 6 rows
  unchanged.
- `verify` on a real bundle: PASS with `invariants_ok: true`; `verify` on a copy whose `outcome.json` was changed to an
  impossible combination and whose `hashes.json` was regenerated: FAIL with a non-zero exit code and the violation printed
  (the hash alone would not catch it).
- Unit tests: the existing ones pass; a new `tests/test_invariants.py` covers the 31 cases plus the schema-enum check.
- Not predicted / open: bundles produced before F-021 (no `oracle_required` field) are not rejected for that field (the
  check runs only when the key exists); older bundles are not available here, so this is untested.

## Linux jinja bundles (predictions committed BEFORE the run)

`run_lab001.sh` on Linux (host mode, `--allow-unverified-provenance`, qualifier `PROVENANCE_UNVERIFIED`) writes 7
bundle folders (oracle before/after/post-fix, case_c_unpinned, f01-f04 as they exist in the runner output).
Prediction: `python3.8 -m reprogate inspect` exits 0 with the invariants reported OK for every bundle that has an
`outcome.json`; `verify` on the oracle "before" bundle passes (hashes, outcome, commit and environment match) and its
invariants are OK; `provenance_sufficient` stays False with the qualifier present (unverified provenance is a valid
combination, rule QUALIFIER).
