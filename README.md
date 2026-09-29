# ReproGate - Python prototype (v0.0.1-proto)

ReproGate turns "an agent says it reproduced the bug" into **replayable executable evidence**:
the reproducer is treated as untrusted, executed by an independent verifier, observed structurally
(not by reading logs), matched against a frozen claim, repeated in fresh processes, and written into
an evidence bundle. It does **not** claim the bug is real: `SYMPTOM_REPRODUCED != BUG_CONFIRMED`. A single run can be a false positive (F-015); only a passing before/after oracle counts as evidence.

This is an early **prototype**, deliberately small:

- Python 3.8+ and the standard library only (Docker is optional and only used by the sandbox mode).
- Exception-type claims only (`wrong_output` / `unexpected_exit` are not implemented).
- Runs reproducers as plain host processes by default (no sandbox); `--sandbox docker` runs them in a network-less,
  read-only container (see `THREAT_MODEL.md`).
- It exists to answer one question with real data: can an independent verifier tell a real reproduction, a clean fix,
  an environment failure and gamed reproducers apart on real bugs?

## Honest status

| item | state |
|---|---|
| unit and end-to-end tests (synthetic libraries) | 68 tests pass on Linux, Python 3.8.20 (6 Docker tests skip when Docker or the image is missing); 52 tests passed on Windows 11 / Python 3.8 earlier (F-016) |
| 9 hand-picked labs on real checkouts (jinja#843, tabulate x2, cachetools x2, more-itertools x2, sortedcontainers, dateutil) | predictions were committed before each run; one prediction missed (more-itertools#707, F-011/F-012, fixed); all rows match now (Linux host mode; jinja#843 also on Windows) |
| claim provenance checked against the raw issue body | verified for jinja#843, tabulate#180, more-itertools#707; unverified for the other labs (their claims come from fix commits) (F-006, F-010, F-016) |
| gate attack round 2 (10 attacks on one lab) | 9 of 10 predictions held; the miss led to a stricter message rule (F-020, F-021). Known weakness: a builtin callable supplied by the reproducer can produce a matching failure; only the before/after oracle rejects it (F-015) |
| Docker sandbox runner (`--sandbox docker`) | Linux only; the 9 labs give the same outcomes as host mode (F-017); the harness still runs in the reproducer's process (`observation_integrity: BEST_EFFORT_IN_PROCESS`); since F-024 a supervisor process validates the observation, which stops cheap file forgery but not a protocol-aware reproducer; since F-026 it also checks TARGET frames against the real source, which a reproducer that names a real file, function and line still passes |
| random sample of bugs the maintainer did not choose (`labs/sample-2026-09/`) | protocol fixed before the draw; 4 issues drawn, 1 executed (click#942, inconclusive), 3 not evaluated (need network or unsafe input); says nothing about accuracy (F-022) |
| environment trust, portable evidence, signing, other claim kinds | not implemented (`environment_trust: UNVERIFIED`) |

The hand-picked labs were chosen by the author, are pure-Python libraries and use exception claims only. They are not a
benchmark and do not show how the tool behaves on arbitrary bugs. Feedback is welcome, see `CONTRIBUTING.md`.

## Quick start (Windows, from this folder)

```
py -3.8 -m unittest discover -s tests -t . -v
powershell -ExecutionPolicy Bypass -File labs\jinja-843\run_lab001.ps1
```

Linux / macOS: `bash labs/jinja-843/run_lab001.sh` (needs git, Python 3.8 and network).
Step-by-step runbook: `labs/jinja-843/README.md`.

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
reprogate/      gate.py (static gate) provenance.py (claim vs raw issue body) harness.py (runs under the
                TARGET interpreter, structured observation) matcher.py outcome.py runner.py (host runner,
                tree hash, env capture) pipeline.py (evaluate / oracle / replay) evidence.py cli.py
tests/          unit + end-to-end tests on a synthetic library
tools/          fetch_issue.py (raw issue body via API), lab_summary.py, run_lab.py, sample_issues.py
labs/<lab>/     claim, reproducer, negative fixtures, expected outcomes (written before the run), results
labs/jinja-843/ also the runbook and the Windows / Linux runners
labs/gate-round2/  attack reproducers, predictions and results
labs/sample-2026-09/  random-sample protocol and draws
findings.md     the only place architecture changes may originate
```

## License

MIT - see [LICENSE](LICENSE).
