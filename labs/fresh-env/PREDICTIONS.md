# Fresh environment per run (F-032, decision_053): predictions committed BEFORE the code and BEFORE the run

Founder decision (2026-09-29, after F-028 and F-031): in host mode every run gets a fresh copy of an environment template
instead of hashing installed packages (a hash is a snapshot and does not stop `sitecustomize`/state left behind); design
must account for the cost of building the environment and for deterministic setup. Docker mode already gets a fresh container
per run and is not changed. Import-phase failures that are not ImportError stay semantic mismatches (decision_054).

Mechanism (planned): `--env-template DIR` (host mode only; `--python` must live inside DIR). Before every run the template
tree hash is compared with the hash taken at the start; a difference aborts the evaluation (ValueError, exit code 2). The
template is copied to a temp directory outside the evidence bundle, the run uses the interpreter inside the copy, the copy is
deleted afterwards. `environment.json` records the mode, the template tree hash and file count; each run records
`env_copy_seconds`; `outcome.json` records `environment_mode` (`FRESH_COPY_PER_RUN` or `SHARED_HOST_ENVIRONMENT`).

Runner: `run_fresh_env.ps1 -Yes` (d01-d03 from `labs/adversarial-round3/` against a template copy in %TEMP%; then the jinja
oracle with the real `.venv` used only as a read-only template). Reference for the "before" state: F-028 (Windows, host mode,
shared environment); it is not re-run.

## Predictions for the change
| item | F-028 (shared environment) | predicted with `--env-template` |
|---|---|---|
| d01 (append to a dependency file) | NO_MATCHING, file hash CHANGED, undetected | NO_MATCHING_REPRODUCTION_FOUND/NONE, 5 COMPLETED; the TEMPLATE file hash is UNCHANGED; environment.json records FRESH_COPY_PER_RUN and a template hash equal to an independent hash of the template |
| d02 (`sitecustomize.py` persistence) | marker length 8 | marker length 0 (the file written in run 1 lives in a copy that is deleted; later runs start clean); NO_MATCHING/NONE |
| d03 (poisoned dependency raising the claimed message) | 5 COMPLETED, only 1 clean completion | 5 COMPLETED and 5 clean completions (no run is poisoned by an earlier one); NO_MATCHING/NONE |
| cost | none | a copy of a ~17 MB venv plus two tree hashes per run: my guess is a few seconds per run; the observed `env_copy_seconds` and total time per 5-run evaluation are recorded, no threshold is decided here |
| determinism | n/a | two evaluations of d01 with the same template give the same template tree hash and the same outcome |
| jinja oracle with the real `.venv` as template | ORACLE PASS | ORACLE PASS (before SYMPTOM_REPRODUCED, after clean completion), invariants OK, the real `.venv` untouched (tree hash before = after) |
| unit tests | 100 OK, 11 skipped | existing ones pass; new `tests/test_fresh_env.py`: a marker written by a reproducer does not persist with a template and does persist without one (control); a reproducer that writes into the template path aborts the next run with ValueError; `--sandbox docker` with a template, and `--python` outside the template, raise ValueError |

Not covered: Linux host mode with a template (untested here), large environments, an environment that cannot be copied, network
access during the copy (none is used), a reproducer that knows the template path and races the hash check.

## F-038 test fix: predictions committed BEFORE the change

Diagnosis (F-038, `labs/linux-2026-09-29/RESULTS.md`): `tests/test_fresh_env.py` builds its venv with `venv.create()`, which copies the
interpreter on POSIX (`symlinks=False`); a shared-library CPython (uv-managed) cannot start from the copy, so every run is ENV_FAILURE.
Founder decision (2026-09-29): change only the test setup to `venv.create(..., symlinks=(os.name != "nt"))`; no change in `reprogate/`.

- Windows (`symlinks` stays False there, so nothing changes): 136 tests OK, 11 skipped; `tests/test_fresh_env.py` 7 of 7 OK.
- Linux, uv CPython 3.8 as root (run by the Linux session after the push): `tests/test_fresh_env.py` 7 of 7 OK; full suite 136 OK,
  0 failures, 0 errors, 0 skipped. Then F-038 is closed as a test-setup problem.
