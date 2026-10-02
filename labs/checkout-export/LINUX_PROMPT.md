# Prompt for a short Linux + Docker session (paste everything below the line into a fresh AI session)

---

You are working on ReproGate (https://github.com/masoudmousavi89/reprogate, a small Python-only, standard-library-only verifier for
bug-reproduction claims). Read `README.md`, `DEVELOPING.md`, `THREAT_MODEL.md`, `findings.md` (F-048 to F-052),
`labs/checkout-export/PREDICTIONS.md` and `RESULTS.md`, and `labs/checkout-sha-docker/results-linux-2026-10-02.md` (the previous Linux
session, whose scripts you can reuse). Project rules: predictions are written and committed BEFORE any run; every surprise becomes a
finding; write what you did not test.

## What changed since the previous Linux session
`--checkout-sha` no longer uses `git worktree`: it writes the exact blobs of the commit into an empty directory with no `.git`
(`reprogate/checkout.py`, F-052), because F-050 showed a worktree is not isolated from the source repository in host mode. And the
Docker `/work` tmpfs now has `mode=1777` (F-051). Your job: confirm both on Linux with real Docker. You do not close req_005 and you
do not change founder decisions.

## Work
1. Create a branch `linux-docker-export` from `main` (commits b4b508b and 5d33f9c and the result commit must be on origin; if not, stop and
   say so). Push only the branch, never `main`.
2. Run the whole suite (`python -m unittest discover -s tests -t .`). Expected: all pass, 0 skipped on Linux (Docker and POSIX tests run,
   including the exec-bit and symlink test of `tests/test_checkout.py`). Record exact counts.
3. Write `labs/checkout-export-linux/PREDICTIONS.md` and commit it FIRST. Predict at least:
   a. F-050 attacks d1-d4 (see `labs/checkout-sha-docker/host_exposure.py`, adapt it, never weaken the real gate) in HOST mode with
      `--checkout-sha`: all now fail (no `.git` to reach), the source `.git` hash is identical afterwards, `git fsck` of the source is clean.
   b. Docker mode: `oracle --before-sha/--after-sha --sandbox docker` on Lab #1 gives ORACLE PASS; tree hashes equal the Windows reference
      values `dbc9cd7de8574222da889f9f94b65d4fd5054e50f4a09128da7b90f10d983b06` (before) and
      `bf8ae6f92378232b5eb2275a763eda0e8ce40ba5766f0b02ffa535d130fee973` (after).
   c. `/work`: with uid 65534 a reproducer can create a file in its working directory and in `/tmp`; a marker written in `/work` in run 1
      is absent in run 2 (fresh container); `docker inspect` shows the tmpfs option `mode=1777` for `/work`; all other flags of
      `reprogate/sandbox.py` are unchanged from the previous session's inspect output (`labs/checkout-sha-docker/docker-inspect-linux.json`).
   d. POSIX export: exec bit and symlinks of a throwaway repository are reproduced; a symlink whose target is `../..` is created as a link
      and is not followed by the tool; a tree with names differing only by case is fine on Linux (distinct files).
   e. Real labs: run the labs whose reproducer is in this repository through `--checkout-sha` in Docker mode, at least `jinja-843`;
      report whether any reproducer writes to its working directory (the open question of F-051).
4. Put scripts in `labs/checkout-export-linux/` (a `.sh` runner) and raw output in `results-linux-*.md`. Findings go into `findings.md`
   as F-053, F-054, ... (one row per surprise, or one row if all held).
5. Push the branch and report: commit hashes, test counts, a table prediction / observed / held-or-miss, and everything not tested.
   Do not claim req_005 is done.

## Hard limits
Do not edit `memory/*.json` or founder-decision text; do not touch `STOP_CRITERIA.md` thresholds; do not weaken the gate, matcher or
supervisor to make a prediction pass; no real secrets or personal data; do not print host environment variables; everything you add must be
reproducible by a script.
