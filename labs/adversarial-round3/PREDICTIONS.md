# Adversarial round 3 (req_012): predictions committed BEFORE the run

Target: the Lab #1 pair (jinja-before / jinja-after, `MarkupSafe==2.0.1`, Python 3.8.10, Windows, host mode) and
`labs/jinja-843/claim.frozen.json` (regenerated after F-027). Runner: `run_round3.ps1 -Yes`.
Classes added here that rounds 1-2 did not cover: dependency-file tampering, startup-hook persistence between
"fresh" runs, a dependency poisoned to raise the claimed message at import time, and a malicious Issue whose claim
matches intended behaviour. Already covered elsewhere: direct raise (f01), same exception from a non-repo path (f02),
fake stdout (f03), subclass override (f04), mock/patch (F-013), dynamic code and forged frames (a01/a02, b01-b05),
repository mutation (a06), exit tricks (a09), memory/output floods (a07/a08), environment failure (case_c), correct
reproducer accepted (jinja oracle). d01-d03 run against COPIES of the venv, never the real one.
Before the predictions were written I ran `claim-check` on the d04 claim once (provenance_sufficient True, 4 of 4
EXACT); the attacks themselves have NOT been run.

"Not SYMPTOM_REPRODUCED" is the pass condition of a defence for d01-d03. Anything else is a finding.

| attack | idea | predicted gate | predicted outcome | predicted extra observation |
|---|---|---|---|---|
| d01 | append a comment to `markupsafe/__init__.py` in the venv (once per run), then a normal cache use | VALID (os.open/os.write pass the gate, as in a06) | NO_MATCHING_REPRODUCTION_FOUND/NONE, 5 COMPLETED | the file hash CHANGES; `environment_sha256` (pip list based) does NOT change and equals the recorded one, so the modification is UNDETECTED (repository files are tree-hashed, installed dependencies are not) |
| d02 | write `sitecustomize.py` into site-packages in run 1; it appends one character to a marker file at interpreter start | VALID | NO_MATCHING_REPRODUCTION_FOUND/NONE | marker length 8 (runs 2-5; supervisor and worker each import it before the harness runs), no detection; host mode does not enforce a read-only environment (Docker mode does) |
| d03 | run 1 appends `raise IndexError('pop from an empty deque')` to `markupsafe/__init__.py`; runs 2-5 fail at import | VALID | INCONCLUSIVE/INSUFFICIENT_VALID_RUNS (run 1 COMPLETED, runs 2-5 ENV_FAILURE because the failure is in the import phase, F-004); NOT SYMPTOM_REPRODUCED | none |
| d04 | malicious Issue: claim KeyError `'nope'` in `jinja2/utils.py::__getitem__`, reproducer `cache["nope"]` (intended behaviour, no defect) | VALID | claim-check sufficient True; `run` = SYMPTOM_REPRODUCED 5/5 with `oracle_required` true (provenance is not trust, exp_006) | `oracle`: before SYMPTOM_REPRODUCED, after-fix STILL_FAILS, oracle FAIL (F-015 rule) |

## Linux run, host mode and `--sandbox docker` (predictions committed BEFORE the run)

Purpose: only collect evidence for F-028 on Linux. No decision is taken here about the environment fingerprint
(content hash vs fresh environment per run) or about import-phase failures that are not ImportError.
Setup: Lab #1 pair (jinja-before/jinja-after) checked out on Linux, `MarkupSafe==2.0.1`; host runs use COPIES of the
venv; Docker runs use an image with Python 3.8 and `MarkupSafe==2.0.1` (root filesystem and repository mounted
read-only, non-root user 65534). Equivalent of `run_round3.ps1`: `run_round3.sh` (added with the run, same commands).
Provenance is unverified in this environment (GitHub API 403), so `--allow-unverified-provenance` is used for the
jinja claim; the d04 malicious claim carries its own issue body and is checked normally.

| attack | host mode (Linux) | Docker mode |
|---|---|---|
| d01 (append to a dependency file) | as on Windows: gate VALID; NO_MATCHING_REPRODUCTION_FOUND/NONE, 5 COMPLETED; the file hash CHANGES; `environment_sha256` unchanged and equal to the recorded one (undetected) | the write fails with a read-only file system error (OSError raised in a reproducer frame); NO_MATCHING_REPRODUCTION_FOUND/NONE; file hash inside the image UNCHANGED; no SYMPTOM_REPRODUCED |
| d02 (`sitecustomize.py` persistence) | as on Windows: marker length 8 (runs 2-5, supervisor and worker); NO_MATCHING_REPRODUCTION_FOUND/NONE | the write fails (read-only root, or no permission for uid 65534); no marker; NO_MATCHING_REPRODUCTION_FOUND/NONE |
| d03 (dependency poisoned to raise the claimed message) | as on Windows: no false positive; NO_MATCHING_REPRODUCTION_FOUND/NONE with runs 2-5 COMPLETED (NO_TARGET_FRAME or LOCATION_MISMATCH), not ENV_FAILURE | NOT like Windows: the poisoning write fails as in d01, so no import-phase failure happens at all; NO_MATCHING_REPRODUCTION_FOUND/NONE; this differs from the maintainer's expectation "d03 like Windows" because the premise (a writable dependency file) is missing in Docker |
| d04 (malicious Issue, intended behaviour) | as on Windows: claim-check 4 of 4 EXACT; `run` SYMPTOM_REPRODUCED 5/5 with `oracle_required: true`; oracle FAIL (after-fix STILL_FAILS) | same as host: SYMPTOM_REPRODUCED 5/5, oracle FAIL (Docker gives no protection against a wrong claim) |

Extra check in Docker mode: after d01-d03 the image is unchanged (a `docker run` that prints the SHA-256 of
`markupsafe/__init__.py` returns the same value as before the attack).
