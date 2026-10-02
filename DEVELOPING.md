# Developer guide

Read this first, then `README.md`, `ARCHITECTURE.md`, `THREAT_MODEL.md` and `findings.md`. The repository is the
only source of truth; nothing important lives outside it.

## 1. What the tool claims (do not exceed it)

ReproGate checks a claim "this reproducer triggers exception X in project P at commit C". It reports
`SYMPTOM_REPRODUCED`, never "bug confirmed". A single run can be a false positive; only a passing before/after oracle
(symptom before the fix, clean completion after it) is evidence. Any text you write (README, results, reports) must
stay inside that limit and must state the limits: exception claims (wrong_output only experimental), small hand-picked samples, no sandbox on
Windows, observation forgeable by a protocol-aware reproducer.

## 2. Working rules (these keep the evidence credible)

1. Architecture changes only with a finding in `findings.md` that cites evidence. IDs are permanent; take the next
   free id after `git pull` (last one at the time of writing: F-026).
2. Pre-registration: write `expected_outcomes.json` (or `PREDICTIONS.md`) and COMMIT it before the first run. Report
   every miss as a finding; never edit a reproducer, claim anchor or prediction to make a run pass. A fix to the
   environment (paths, interpreter) is allowed only as a separate, labelled second run; keep the first run's result.
3. Random-sample rules are in `labs/sample-2026-09/PROTOCOL.md`: draw once, the first result counts, no redraws, hard
   cases stay in the table as `NOT_EVALUATED` with a reason.
4. Never run a reproducer that needs a real network service or unsafe input on your own machine in host mode.
5. Before every push: `git pull --rebase origin main`; run the tests; check the diff and the log for personal paths,
   user names and emails (for example `git diff origin/main..HEAD | grep -niE 'C:\\\\Users|@'`). Commits use the
   maintainer's identity with no extra trailers. Never force-push `main`.
6. Keep tool output short in reports; summarise, do not paste logs.

## 3. Commands

```
py -3.8 -m unittest discover -s tests -t . -v          # Windows; Linux: python3.8 -m unittest discover -s tests -t .
python -m reprogate gate --reproducer r.py              # static check only
python -m reprogate run --repo <checkout> --python <target python> --claim claim.json --reproducer r.py \
       --out <dir> --allow-host-execution [--allow-unverified-provenance]
python -m reprogate oracle --before-repo A --after-repo B --python <py> --claim ... --reproducer ... --out <dir> ...
python -m reprogate run --sandbox docker --image <image> --repo <checkout> --claim ... --reproducer ... --out <dir>
python tools/lab_summary.py --evidence <dir> --expected labs/<lab>/expected_outcomes.json   # compare with predictions
python tools/run_lab.py ...      # clones the project, builds worktrees and a venv, runs oracle + fixtures
```
Jinja lab runners: `labs/jinja-843/run_lab001.ps1` (Windows) and `run_lab001.sh` (Linux/macOS). Evidence folders and
raw issue files are gitignored; keep them out of commits.

## 4. How the pieces fit

`claim-check` (provenance: claim anchors must appear in the raw issue body) -> `gate` (static check, the first line of defence only, not a security boundary) ->
`evaluate`: environment capture, tree hash, N fresh runs of `harness.py` (supervisor + worker, F-024) -> `matcher`
per run (origin, type, message, location) -> `outcome` aggregation -> evidence bundle with hashes -> `oracle` combines
a before and an after evaluation. Rules in the code, each backed by a finding: origin needs an authentic TARGET frame
and no REPRODUCER frame after it (F-011/F-012 for the PEP 479 exception); a claim with a message must match the
message (F-020/F-021); `raise` is allowed only inside a function body (F-011); the observation file is trusted only
when the harness exit code is 0 (F-024).

## 5. Adding a lab

1. Pick the bug and write down how it was chosen (random draw or hand-picked; say so).
2. `labs/<name>/claim.json`: `claim` (exception_type, optional message, optional location), `target`
   (affected_commit = first parent of the fix, fix_commit), `issue` (repo, number or null), optional `env`
   (`pip`: explicit pinned packages only; `pythonpath`: for example `["src"]`). Never install the target repository itself.
3. `repro.py` (from the issue text), `fixtures/` (direct raise, same exception type raised in user code, fake traceback
   on stdout, subclass override), `expected_outcomes.json` with predictions. Commit. Only then run.
4. Record results in `labs/<name>/` or a `results-*.md`, and a finding for every surprise.

## 6. Environment notes

- Target code must run on Python 3.8 (the tests include a 3.8-syntax check). Some projects need a newer interpreter
  (recent more-itertools needs >= 3.10); say which interpreter was used.
- Some projects use a `src/` layout: use `env.pythonpath`. Some need one extra package (for example `six`).
- Docker mode is tested on Linux only. Behind a TLS-intercepting proxy `docker build` cannot reach PyPI: download the
  wheels on the host and install them with `--no-index`.
- On Windows there are no POSIX signals or `/proc`: the forgery tests in `tests/test_observer_split.py` are skipped
  there. Without Docker, 11 tests skip (6 Docker, 5 POSIX-only). The process-tree kill uses `taskkill`.
- GitHub API access is needed for raw issue bodies (`tools/fetch_issue.py`); without it provenance stays unverified.

## 7. Open technical work (highest value first)

1. Observation can still be forged by a reproducer that re-implements the result protocol and names a real file,
   function and line (attack b05, F-026; the fake-frame variant b02 is now rejected). A call-chain rule was tried on
   paper and dropped (implicit calls make it unsound). A sound fix needs kernel-level tracing or an unforgeable
   second signal.
2. Provenance is verified for only 3 of the 9 hand-picked labs; the other claims come from fix commits.
3. click#942 (random sample) was inconclusive: the reproducer used a completion protocol that does not fit the version
   under test. A corrected reproducer would be a new, labelled run.
4. `wrong_output` is EXPERIMENTAL (F-039): synthetic cases only, exact equality, a protocol-aware reproducer can still
   forge a return (as for exceptions, F-026); no real bug has been evaluated with it.
5. `--checkout-sha` is tested on Windows only (F-048); a worktree shares the source repository `.git` (host mode exposure not mitigated).
6. Docker mode on Windows/macOS; a stronger sandbox (gVisor / VM) than a shared-kernel container.
