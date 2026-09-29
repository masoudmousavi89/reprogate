# Adversarial round 3: results (2026-09-29; predictions in PREDICTIONS.md, committed first as 6cbfb90)

Windows 11, Python 3.8.10, host mode, Lab #1 pair (`MarkupSafe==2.0.1`), claim = regenerated `claim.frozen.json`.
d01-d03 ran against copies of the venv in `%TEMP%` (deleted afterwards). Raw evidence folder deleted (personal paths);
paths below are masked as `<HOME>`.

| attack | gate | outcome | as predicted |
|---|---|---|---|
| d01 tamper a dependency file | VALID | NO_MATCHING_REPRODUCTION_FOUND/NONE, 5 COMPLETED | yes |
| d02 sitecustomize persistence | VALID | NO_MATCHING_REPRODUCTION_FOUND/NONE, 5 COMPLETED | yes |
| d03 poisoned dependency raises the claimed message at import | VALID | NO_MATCHING_REPRODUCTION_FOUND/NONE, 5 COMPLETED (1 clean completion) | **no** (predicted INCONCLUSIVE/INSUFFICIENT_VALID_RUNS with runs 2-5 ENV_FAILURE) |
| d04 malicious Issue, intended behaviour | VALID | claim-check sufficient True; run SYMPTOM_REPRODUCED 5/5, `oracle_required: yes`; oracle FAIL (before SYMPTOM_REPRODUCED, after STILL_FAILS) | yes |

Extra observations
- d01: `markupsafe/__init__.py` hash changed (`file_hash_changed=True`), while the environment fingerprint before, after and as
  recorded in the bundle is identical (`env_sha_before_equals_after=True`, `recorded_env_equals_after=True`). The modification of
  an installed dependency is not detected: the repository is tree-hashed, installed dependencies are only listed by name and version.
- d02: the marker file grew by 8 characters (runs 2-5, supervisor and worker each executed the planted `sitecustomize.py` at
  interpreter start, before the harness). Host mode does not keep the environment read-only between "fresh" runs. Docker mode
  (read-only root filesystem) was not run on Windows.
- d03: runs 2-5 recorded `phase: import`, exception IndexError with anchors `exception_type` and `message` matched, reasons
  `NO_TARGET_FRAME` and `LOCATION_MISMATCH`, status COMPLETED, `symptom_match: false`. So the defence held through the location
  and frame requirement, not through ENV_FAILURE: an import-phase failure that is not an ImportError is counted as a completed
  run that did not match (it stays in the semantic denominator). No false positive.
- d04: provenance passed (4 of 4 EXACT, sufficient) for a claim that describes intended behaviour; only the before/after oracle
  rejected it, as in F-015.

Not covered: the same attacks in Docker mode; kernel-level tampering; d03 with a poisoned dependency that raises from inside a
target module (not possible without writing the repository, which the tree hash catches).
