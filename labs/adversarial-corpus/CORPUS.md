# Adversarial corpus index (req_012)

The corpus is a set of committed attack files and fixtures spread over several labs, each with a recorded result. This file maps every
class named in req_012 to those files and results, and states what is NOT closed. A class counts as covered only when a committed file
exists AND a result of a real run is recorded (in a `RESULTS.md`, a lab results file or a finding). The matrix was built by reading the
result files listed here on 2026-10-03; it did not re-run every attack. Outcomes are as recorded at the time; behaviour changed later
only where a finding says so (F-021, F-024, F-026, F-032, F-033).

Outcome names: NO_MATCH = `NO_MATCHING_REPRODUCTION_FOUND`, REJECTED = `NOT_EVALUATED / REPRODUCER_REJECTED`, SYMPTOM = `SYMPTOM_REPRODUCED`.

| req_012 class | committed files | recorded result | evidence | what is not closed |
|---|---|---|---|---|
| direct raise | `labs/jinja-843/fixtures/f01_direct_raise.py`, same name in `cachetools-27`, `cachetools-63`, `more-itertools-707` | REJECTED (`DIRECT_RAISE`) on every lab | F-009, F-016, F-011 | the gate rejects any `raise`, including a legitimate callback raise (F-011, a known cost) |
| same exception from a non-repository path | `jinja-843/fixtures/f02_direct_deque_popleft.py`, `cachetools-*/fixtures/f02_stdlib_same_type.py`, `gate-round2/attacks/a03_catch_then_builtin_error.py` | NO_MATCH (no authentic TARGET frame) | F-009, F-012, F-020 | PEP 479 conversion is accepted only by a closed whitelist (F-012, F-015) |
| fake traceback on stdout | `f03_fake_traceback_stdout.py` in four labs | NO_MATCH (verdict is never built from stdout/stderr) | F-009, F-013, F-014 | none known |
| callback / subclass trick | `jinja-843/fixtures/f04_subclass_override.py`, `more-itertools-707/fixtures/f04_throw_into_library_generator.py`, `gate-round2/attacks/a04_builtin_callback_crafts_message.py`, `a10_unicode_lookalike_message.py` | f04 jinja: NO_MATCH; a04 and a10: SYMPTOM 5 of 5 (false positive) with oracle FAIL; more-itertools f04: residual limitation, mitigated by the oracle | F-013, F-015, F-020, F-021 | a single run cannot separate a user-supplied failing callable from a real bug; only the before/after oracle does (F-015); the message anchor is weak when location matches (F-020) |
| mock / monkeypatch of the target | `tests/test_gate.py::test_mocking_and_patching_rejected`, `jinja-843/fixtures/f05_patch_target.py` (added 2026-10-03), `labs/adversarial-corpus/run_f05.py` | real gate: REJECTED (`PATCHES_TARGET`, line 9, no run); gate bypassed: NO_MATCH 5 of 5 (the frame is the reproducer's own) | F-013 (scratch attempts), this lab (7678108 predictions first; log `labs/adversarial-corpus/run-windows-2026-10-03.log`) | other patching forms (for example writes through `vars()` or `__dict__`) were not tried here |
| dynamic code / forged filename | `gate-round2/attacks/a01_hidden_builtins_forged_frame.py`, `a02_hidden_builtins_real_globals.py`, `observer-split/attacks/b01`-`b05` | a01, a02: gate VALID, NO_MATCH; b01-b04: not SYMPTOM; **b05 (forge a plausible frame): SYMPTOM 5 of 5 in host and Docker** | F-020, F-023, F-024, F-026, F-030, F-031 | **b05 is accepted and is a documented limitation** (needs kernel-level tracing; ROADMAP after alpha) |
| source mutation | `gate-round2/attacks/a06_tamper_repo_file.py`, `adversarial-round3/d01_tamper_dependency_file.py`, `d02_sitecustomize_persistence.py` | a06: INCONCLUSIVE / REPOSITORY_MODIFIED (5 INVALID); d01, d02 on a shared host environment: NOT detected (NO_MATCH, 5 COMPLETED); with `--env-template` the state does not reach later runs | F-020, F-028, F-031, F-032, F-037 | the shared-environment mode still does not detect a changed dependency (the fingerprint is names and versions); `--env-template` is opt-in; a writable dependency inside a root container (open in F-031) |
| exit manipulation | `gate-round2/attacks/a09_exit_with_claim_text.py`; the exit code is never used (F-003) | NO_MATCH | F-003, F-013, F-020 | none known |
| dependency poisoning | `adversarial-round3/d01`, `d02`, `d03_poison_dependency_claim_text.py` | d01-d03 never gave SYMPTOM; d03 gave 5 COMPLETED instead of the predicted ENV_FAILURE (a recorded miss) | F-028, F-031, F-032 | as in the row above |
| malicious Issue (snippet + traceback consistent with the claim) | `adversarial-round3/d04_malicious_issue_reproducer.py`, `adversarial-round3/malicious-issue/` | claim-check sufficient; SYMPTOM 5 of 5, `oracle_required: yes`; the oracle FAILS (after-fix STILL_FAILS) | F-028, F-031 | a single run is not evidence; only a passing oracle is (F-015, F-020) |
| environment failure | `labs/jinja-843/run_lab001.*` case `case_c_unpinned` (MarkupSafe 2.1.5), `labs/wheelhouse/` | NOT_EVALUATED / ENVIRONMENT_UNAVAILABLE (never a mismatch) | F-009, F-016, F-047 | none known |
| a correct reproducer is accepted | `labs/jinja-843/repro.py` and the `repro.py` of the other labs | oracle PASS: before SYMPTOM, after clean completion (recorded for jinja-843, more-itertools-falsy and sortedcontainers-eq; the other labs are in the rows of F-014 and F-019) | F-009, F-016, F-034, F-047, F-048, F-053 | click-942 was inconclusive for a protocol reason (F-022); the random sample had 0 evaluable draws in most rounds |

Beyond the list: `a05_flaky_real_trigger` (SYMPTOM_REPRODUCED_FLAKY), `a07_memory_bomb` (INCONCLUSIVE / INSUFFICIENT_VALID_RUNS),
`a08_output_flood` (NO_MATCH, 496 KB bundle) are also recorded in `gate-round2/RESULTS.md`.

## Reading
Every class named in req_012 has a committed file and a recorded real result. No attack produced a SYMPTOM_REPRODUCED bundle that also
passes the oracle, except what is stated: **b05** (accepted; documented limitation) and the false positives a04/a10/d04 (single runs
that the oracle rejects). That is a statement about this corpus, not a security claim: the corpus is small, hand-written, and the gate is
a first line, not a boundary (F-020).

## How to re-run
Windows: `labs/gate-round2/` (Docker), `labs/adversarial-round3/run_round3.ps1`, `labs/observer-split/`, `labs/jinja-843/run_lab001.ps1`,
`labs/adversarial-corpus/run_f05.py`. Linux: the `.sh` runners in the same folders. There is no single runner for the whole corpus; that is a
gap, not a hidden feature.
