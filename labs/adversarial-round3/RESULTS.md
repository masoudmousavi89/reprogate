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

## Linux run, host mode and Docker mode (2026-09-29)

Predictions: section "Linux run, host mode and `--sandbox docker`" of `PREDICTIONS.md` (f64c0b3). Runner: `run_round3.sh host|docker`
(added with this run; same commands as `run_round3.ps1`). Lab #1 pair on Linux, CPython 3.8.20, `MarkupSafe==2.0.1`, unverified
provenance for the jinja claim (`PROVENANCE_UNVERIFIED`); d04 claim-check normal. Docker image `reprogate-jinja-pinned:local`
(python:3.8-slim + MarkupSafe 2.0.1 wheel, `--no-index`).

| attack | mode | predicted | actual | match |
|---|---|---|---|---|
| d01 | host | NO_MATCHING; file hash changes; env sha unchanged and equal to recorded | NO_MATCHING_REPRODUCTION_FOUND, 5 COMPLETED; `file_hash_changed=True env_sha_before_equals_after=True recorded_env_equals_after=True` (tampering undetected) | yes |
| d01 | Docker | write fails (OSError in a reproducer frame); NO_MATCHING; image file hash unchanged | NO_MATCHING_REPRODUCTION_FOUND; exception `PermissionError [Errno 13]` (uid 65534 has no write permission; the prediction said "read-only file system", PermissionError is also an OSError); image SHA-256 of `markupsafe/__init__.py` identical before and after | yes (error text differs) |
| d02 | host | marker length 8; NO_MATCHING | `marker_writes=8`; NO_MATCHING_REPRODUCTION_FOUND, 5 COMPLETED | yes |
| d02 | Docker | write fails, no marker; NO_MATCHING | NO_MATCHING_REPRODUCTION_FOUND; `OSError [Errno 30] Read-only file system` on `sitecustomize.py`; image has no `sitecustomize.py` afterwards | yes |
| d03 | host | NO_MATCHING; runs 2-5 COMPLETED, not ENV_FAILURE | NO_MATCHING_REPRODUCTION_FOUND, 5 COMPLETED (1 clean completion = run 1, before the poisoning), no ENV_FAILURE | yes |
| d03 | Docker | poisoning write fails as in d01; NO_MATCHING (differs from the maintainer's "like Windows" expectation: premise absent) | NO_MATCHING_REPRODUCTION_FOUND, 5 COMPLETED with `PermissionError [Errno 13]`; image file hash unchanged; no import-phase failure occurred | yes |
| d04 | host | claim-check 4 of 4 EXACT; SYMPTOM_REPRODUCED 5/5, `oracle_required` true; oracle FAIL | `provenance_sufficient: True`; SYMPTOM_REPRODUCED, 5 of 5 matching; oracle before SYMPTOM_REPRODUCED, after SYMPTOM_REPRODUCED, post-fix STILL_FAILS, ORACLE FAIL | yes |
| d04 | Docker | same as host | SYMPTOM_REPRODUCED 5/5, `oracle_required: true`; ORACLE FAIL (post-fix STILL_FAILS) | yes |

Evidence only, no decision taken (as instructed): (1) the environment fingerprint stays name/version based; in host mode d01 and d02 show the
gap again on Linux (the tampered file is not detected, sitecustomize persists between "fresh" runs); Docker mode closes both only because the
image is root-owned and mounted read-only, not because the tool detects tampering. (2) Import-phase failures that are not ImportError stay
COMPLETED/NO_MATCHING in host mode (d03); in Docker mode the situation does not arise. (3) Docker gives no protection against a wrong claim (d04).
Not covered: a dependency directory that is writable inside the container (for example an image running as root or a volume mounted read-write).
