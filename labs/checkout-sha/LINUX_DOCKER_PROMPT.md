# Prompt for a Linux session with Docker (paste everything below the line into a fresh Claude session)

---

You are working on ReproGate (https://github.com/masoudmousavi89/reprogate, a small Python-only, standard-library-only
verifier for bug-reproduction claims). Read `README.md`, `DEVELOPING.md`, `ARCHITECTURE.md`, `THREAT_MODEL.md`, `findings.md`
(especially F-017, F-018, F-030, F-031, F-037, F-047, F-048) and `labs/checkout-sha/PREDICTIONS.md` and `RESULTS.md` first.
Rule of the project: architecture changes only with a finding that cites evidence; predictions are written and committed BEFORE
any run; every surprise becomes a finding; write what you did not test.

## Context
On Windows (no Docker there) the tool got `run --checkout-sha SHA` and `oracle --before-sha/--after-sha`: a fresh detached
`git worktree` of a full 40-hex SHA, removed afterwards (F-048, `reprogate/checkout.py`, `tests/test_checkout.py`). The Docker
part of requirement req_005 (verification sandbox: network off, read-only `/repo`, `/repro` and environment, ephemeral `/work`
and `/tmp`, no secrets, resource limits, fresh container per run, repository tree hash before == after) has evidence only from
F-017 and F-037, from before this change. Your job is to test, on Linux with real Docker, what is still unproven. You do not
close req_005 and you do not change founder decisions: you produce evidence and findings.

## Environment you can expect (check, do not assume)
Linux, Docker, CPython 3.8 via `uv python install 3.8`, git. In an earlier cloud session `docker build` could not reach PyPI
(TLS-intercepting proxy, F-018) and Docker Hub rate-limited; the image `mirror.gcr.io/library/python:3.8-slim` worked, with the
MarkupSafe 2.0.1 wheel downloaded on the host and installed `--no-index` (see `labs/jinja-843/docker/` and
`labs/adversarial-round3/run_round3.sh`). Use the same approach if you hit the same limits, and say so in the findings.
Lab #1 layout and commits: `labs/jinja-843/run_lab001.sh` (SHAs 81825095d24f4dbccb40f787fff70db54989b91c and
9a7dd7b28b50fd8adc019ab2702b50ae5c6ed782, clone of https://github.com/pallets/jinja).

## Work, in this order
1. Branch from `main` (the commits 1c17a7c, 2547826 and later must be on origin; if they are not, stop and say so). Work on a
   new branch named `linux-docker-checkout`. Do NOT push to `main` and do NOT merge; push only the branch.
2. Run the whole unit test suite on Linux (`python -m unittest discover -s tests -t .`). Expected: the new
   `tests/test_checkout.py` passes (9 tests), the Docker tests run instead of skipping. Record the exact counts.
3. Write `labs/checkout-sha-docker/PREDICTIONS.md` and commit it FIRST. Predictions to write (change them if you reason
   differently, but write them before running):
   a. `oracle --before-sha ... --after-sha ... --sandbox docker --image IMG` on Lab #1 gives ORACLE PASS; the worktrees are
      removed; `git worktree list` of the source is back to one entry; source HEAD and tree unchanged.
   b. In the container `/repo` is read-only; the worktree's `.git` is a file pointing to a host path that is not mounted, so
      `git -C /repo status` fails inside the container (check with a throwaway `docker run` using the same mounts the tool
      uses: read `reprogate/sandbox.py` for them, do not guess).
   c. A reproducer that tries to write into `/repo` (tracked file), into `/repo/.git`, and into the host path named in the
      `.git` file: all fail or have no effect on the host; the source repository is byte-identical afterwards
      (hash `.git` and the working tree before and after).
   d. Host mode (no Docker) on Linux with `--checkout-sha`: a reproducer that writes to the path named in the worktree's `.git`
      file DOES modify the source repository's `.git/worktrees/...` metadata. This is the exposure named in PREDICTIONS.md of
      `labs/checkout-sha/`. Predict whether it can also damage objects. Use a throwaway local repository (not the pallets clone)
      and a test copy of the gate-bypassing helper pattern used in `labs/adversarial-round3/` (gate=False in a unit-test style
      script, never weaken the real gate).
   e. Re-verify, in one consolidated run with `docker inspect` output saved, every clause of req_005 for the Docker mode:
      network none, read-only root, caps dropped, no-new-privileges, non-root UID, memory/cpu/pids limits, tmpfs `/tmp`,
      disposable `/work`, fresh container per run (different container ids), no secrets (list the environment seen inside the
      container; compare with `reprogate/runner.py` `env_names()`), tree hash before == after.
   f. Linux line endings: the worktree equals `git archive` of the same SHA byte for byte (same method as
      `labs/checkout-sha/run_checkout_sha.ps1`).
4. Run it. Put scripts in `labs/checkout-sha-docker/` (a `.sh` runner like `run_round3.sh`), raw outputs in a `results-linux-*.md`.
5. Findings: add rows to `findings.md` as F-049, F-050, ... (one per surprise, or one row if all predictions held). If (d) shows
   real damage, say so plainly and propose, but do not implement, the fallback (`git archive` into an empty directory instead of
   a worktree) as an option for the founder.
6. Push the branch and report: commit hashes, test counts, a table prediction / observed / held-or-miss, and everything you did
   not test. Do not claim req_005 is done; say which clauses now have Linux Docker evidence.

## Hard limits
- Do not edit `memory/*.json` or any founder-decision text; do not change thresholds in `STOP_CRITERIA.md`.
- Do not weaken the static gate, the matcher or the supervisor to make a prediction pass.
- No real secrets, tokens or personal data anywhere; do not print environment variables of the host.
- Everything in `labs/` that you add must be reproducible by a script.
