# ReproGate - Python prototype (experimental)

ReproGate turns "an agent says it reproduced the bug" into **replayable executable evidence**:
the reproducer is treated as untrusted, executed by an independent verifier, observed structurally
(not by reading logs), matched against a frozen claim, repeated in fresh processes, and written into
an evidence bundle. It does **not** claim the bug is real: `SYMPTOM_REPRODUCED != BUG_CONFIRMED`. A single run can be a
false positive (F-015); only a passing before/after oracle counts as evidence.

> **Status: experimental.** The accuracy of the verifier on bugs it was not tuned on has **not been measured**
> (see [Measurement](#measurement)). It is **not a security boundary**: in the default host mode a reproducer runs
> as a normal process on your machine (see `THREAT_MODEL.md`). Only run reproducers you have read.

This is an early **prototype**, deliberately small:

- Python 3.8+ and the standard library only (Docker is optional and only used by the sandbox mode).
- Claim kinds: `exception` (a call raises the reported exception); `wrong_output` (a function returns a wrong value)
  is EXPERIMENTAL, version 1, tested on synthetic cases only (F-039, F-040); every other kind is UNSUPPORTED.
- Runs reproducers as plain host processes by default (no sandbox); `--sandbox docker` runs them in a network-less,
  read-only container (Linux); `--env-template` gives every host-mode run a fresh copy of the environment (F-032).
- It exists to answer one question with real data: can an independent verifier tell a real reproduction, a clean fix,
  an environment failure and gamed reproducers apart on real bugs?

## Honest status

| item | state |
|---|---|
| unit and end-to-end tests (synthetic libraries) | 160 tests. Windows 11 / Python 3.8.10: OK, 11 skipped (5 POSIX-only, 6 Docker). Linux / CPython 3.8.20 with Docker: OK, 0 skipped (F-042, 48f93a4) |
| 9 hand-picked labs on real checkouts (jinja#843, tabulate x2, cachetools x2, more-itertools x2, sortedcontainers, dateutil) | predictions were committed before each run; one prediction missed (more-itertools#707, F-011/F-012, fixed). Linux host mode: labs 2-9 give 33 of 33 predicted rows (F-037). jinja#843: 6 of 6 rows on Windows (also from a fresh clone, with pre-built checkouts) and on Linux |
| claim provenance checked against the raw issue body | verified for jinja#843 and tabulate#180; more-itertools#707 is INSUFFICIENT under the anchor guard (its `RuntimeError` anchor occurs twice in the raw body); unverified for the other labs (their claims come from fix commits) (F-006, F-010, F-016, F-027) |
| attacks on the verifier | gate round 2: 9 of 10 predictions held (F-020, F-021). Observation forgery: cheap file forgery closed (F-024), fake frames rejected (F-026), a reproducer that imitates the protocol with a real file, function and line still passes (b05, F-030). Round 3 (dependency tampering, `sitecustomize`, poisoned dependency, malicious issue): no false accept in host or Docker mode, but the malicious-issue claim is rejected only by the before/after oracle (F-028, F-031) |
| Docker sandbox runner (`--sandbox docker`) | Linux only; same outcomes as host mode on the labs (F-017, F-037); the harness still runs in the reproducer's process (`observation_integrity: BEST_EFFORT_IN_PROCESS`) |
| evidence bundles | `inspect` and `verify` check hashes, cross-field invariants and bundle structure; exit code 1 = invalid bundle or failed verify, 2 = incomplete input (F-029, F-035, F-036) |
| random samples of bugs the maintainer did not choose | `labs/sample-2026-09/`: 4 issues drawn, 1 executed, inconclusive (F-022). `labs/sample-v3/`: coverage M4 = 6 of 30 = 20 %, below the pre-registered 25 %, so work moved to `wrong_output`; M1/M2 not measured (see below) |
| environment trust, signing, automatic claim extraction, an investigator agent, `unexpected_exit` | not implemented (`environment_trust: UNVERIFIED`); see `ROADMAP.md` |

The hand-picked labs were chosen by the author, are pure-Python libraries and use exception claims only. They are not a
benchmark and do not show how the tool behaves on arbitrary bugs.

## Measurement

Stop / continue criteria were written before any benchmark run: `STOP_CRITERIA.md` (false accept rate M1, true accept
rate M2, coverage M4, thresholds, minimum sample). Current state:

- M4 (coverage on randomly drawn issues with a traceback): 6 of 30 = 20 % -> rescope, not a stop.
- M1 / M2: **not measured.** Only 6 of the drawn bugs were evaluable (the minimum is 10), and labelling was stopped
  because no independent programmer was available to label reproducers. The reproducers written for it are archived
  unlabelled and are not data (`labs/sample-v3/DEVIATIONS.md`).
- The verdict is due by 2026-10-13 and is expected to be INCONCLUSIVE. Until a BUILD verdict exists, no accuracy,
  precision or reliability figure is claimed anywhere.

## Help wanted

The two things this project cannot produce by itself:

1. **Independent labels.** Programmers who read an issue, a reproducer and its output and say whether the reproducer
   shows the reported bug for the reported reason.
2. **Reproducers the code was not tuned on**, correct or wrong, written from issue text alone - and bypasses: a
   reproducer that gets `SYMPTOM_REPRODUCED` without really triggering the bug is a valuable bug report.

Also useful: real bugs with a wrong return value and a regression test in the fix (for `wrong_output`), runs on
macOS, and criticism of the idea. See `CONTRIBUTING.md`. Security problems: `SECURITY.md`.

## Quick start (Windows, from this folder)

```
py -3.8 -m unittest discover -s tests -t . -v
powershell -ExecutionPolicy Bypass -File labs\jinja-843\run_lab001.ps1
```

The lab runner expects the two Jinja checkouts and virtual environments described in `labs/jinja-843/README.md`.
Linux / macOS: `bash labs/jinja-843/run_lab001.sh` (needs git, Python 3.8 and network).

## Commands

```
python -m reprogate claim-check --claim claim.json --issue-body issue.body.md --out claim.frozen.json
python -m reprogate gate        --reproducer repro.py            # static check only, never executes
python -m reprogate run         --repo <checkout> --python <target python> --claim claim.frozen.json \
                                --reproducer repro.py --out evidence/case1 --allow-host-execution
python -m reprogate oracle      --before-repo <A> --after-repo <B> --python <py> --claim ... --reproducer ... \
                                --out evidence/oracle --allow-host-execution
python -m reprogate verify      --evidence evidence/case1 --repo <checkout> --python <py> --allow-host-execution
python -m reprogate inspect     --evidence evidence/case1
```

`--allow-host-execution` is mandatory on purpose for host mode; without it the tool refuses to run anything.

Docker mode (Linux): `python -m reprogate run --sandbox docker --image <image with Python and the target's dependencies> --repo <checkout> --claim ... --reproducer ... --out ...` (no `--python`, no `--allow-host-execution`). Example images: `labs/jinja-843/docker/`.

## Layout

```
reprogate/      gate.py (static gate) provenance.py (claim vs raw issue body) claims.py (claim kinds)
                harness.py (runs under the TARGET interpreter, structured observation) matcher.py outcome.py
                invariants.py runner.py (host runner, tree hash, env capture) sandbox.py pipeline.py
                (evaluate / oracle / replay) evidence.py cli.py
schema/         result.schema.json (documentation of the outcome contract)
tests/          unit + end-to-end tests on synthetic libraries
tools/          fetch_issue.py (raw issue body via API), lab_summary.py, run_lab.py, sample_issues.py, pypi_pool.py
labs/<lab>/     claim, reproducer, negative fixtures, expected outcomes (written before the run), results
labs/jinja-843/ also the runbook and the Windows / Linux runners
labs/sample-*/  random-sample protocols, draws, checklists and deviations
findings.md     the only place architecture changes may originate
STOP_CRITERIA.md  pre-registered stop / continue criteria
```

## License

MIT - see [LICENSE](LICENSE).
