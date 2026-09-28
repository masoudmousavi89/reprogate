# ReproGate - Python prototype (v0.0.1-proto)

ReproGate turns "an agent says it reproduced the bug" into **replayable executable evidence**:
the reproducer is treated as untrusted, executed by an independent verifier, observed structurally
(not by reading logs), matched against a frozen claim, repeated in fresh processes, and written into
an evidence bundle. It does **not** claim the bug is real: `SYMPTOM_REPRODUCED != BUG_CONFIRMED`. A single run can be a false positive (F-015); only a passing before/after oracle counts as evidence.

This folder is a **Lab #1 prototype**, deliberately small:

- Python 3.8+ only, standard library only (no Go, no Docker, no pip install).
- Exception-type claims only (`wrong_output` / `unexpected_exit` are not implemented).
- Runs reproducers as **plain host processes - there is no sandbox** (see `THREAT_MODEL.md`).
- It is not the Go/Docker core described in the design file; it exists to answer one question
  with real data: does the verifier tell a real reproduction, a clean fix, an environment failure and
  gamed reproducers apart on pallets/jinja#843?

## Honest status

| item | state |
|---|---|
| unit + end-to-end tests on a *synthetic* library (gate, matcher, outcome, forged frames, tree hash, timeouts, env failure, oracle, replay) | written, pass on Python 3.12 in the build sandbox |
| the same tests on Python 3.8.10 / Windows 11 | pass (43 tests, 2026-09-29) |
| real Jinja checkouts, Linux, Python 3.8.20 + MarkupSafe pin | run 2026-09-28: all 7 expected outcomes matched, claim provenance unverified (F-009, F-010); see `labs/jinja-843/results-linux-2026-09-28.md` |
| same lab on Windows via `run_lab001.ps1`, with the raw issue body fetched and claim-check passed | run 2026-09-29: 52 unit tests OK, all 6 rows matched, provenance verified for jinja-843 (F-016) |
| Docker / sandbox runner | **does not exist** |
| environment trust, portable evidence, signing | not implemented (`environment_trust: UNVERIFIED`) |

Five labs (jinja#843, tabulate x2, cachetools, more-itertools; see `labs/`) with predictions written before each run are not a benchmark. Provenance of the
claim against the raw issue body is still unverified (F-006, F-010). Feedback is welcome, see `CONTRIBUTING.md`.

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

`--allow-host-execution` is mandatory on purpose; without it the tool refuses to run anything.

## Layout

```
reprogate/      gate.py (static gate) provenance.py (claim vs raw issue body) harness.py (runs under the
                TARGET interpreter, structured observation) matcher.py outcome.py runner.py (host runner,
                tree hash, env capture) pipeline.py (evaluate / oracle / replay) evidence.py cli.py
tests/          unit + end-to-end tests on a synthetic library
tools/          fetch_issue.py (raw issue body via API), lab_summary.py
labs/jinja-843/ claim, reproducer, 4 harmless negative fixtures, expected outcomes, runner, runbook
findings.md     the only place architecture changes may originate
```

## License

MIT - see [LICENSE](LICENSE).
