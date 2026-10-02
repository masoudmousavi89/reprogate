# Checkout of an exact SHA: results (Windows, py -3.8.10, Git for Windows, 2026-10-02)

Predictions and design: `PREDICTIONS.md`, committed first as 1c17a7c. Code and tests: 2547826. Runner `run_checkout_sha.ps1`, log
`run-windows-2026-10-02.log`.

## Unit tests (new `tests/test_checkout.py`, 9 tests) and the whole suite
179 tests OK, 11 skipped (the same 11 as before: 6 Docker, 5 POSIX-only); before the change 170 OK.

## Predictions vs observed
| item | predicted | observed |
|---|---|---|
| full SHA, files are those of the commit even if the source is dirty or at another commit | yes | held (unit test with a dirty source tree and an untracked file; source tree hash unchanged) |
| abbreviation, branch, tag, `HEAD`, 39/41 hex, non-hex, revision expression | ValueError, exit 2, nothing created | held (unit tests; CLI: abbreviated SHA and `master` give exit 2, worktrees stay at 1) |
| unknown SHA, SHA of a tree or blob | ValueError, nothing left behind | held (unit tests) |
| cleanup, also when the evaluation raises; source HEAD and tree unchanged | yes | held; `checkout.json` says `cleanup: REMOVED`, worktrees 1 before and after, source head and tree unchanged |
| record in `environment.json` | `checkout` object there | MISS (design detail): the record is a separate bundle file `checkout.json` (written after the runs, so it can hold the cleanup result; covered by `hashes.json`); `environment.json` keeps its old shape and has `git.commit` equal to the SHA |
| reproducer edits a tracked file of the checkout | run status REPOSITORY_MODIFIED | wording miss only: runs are INVALID and the outcome is INCONCLUSIVE / REPOSITORY_MODIFIED, as for `--repo` today; source tree unchanged |
| Lab #1 oracle from two SHAs, real `.venv` as template | ORACLE PASS | held: before SYMPTOM_REPRODUCED, after NO_MATCHING_REPRODUCTION_FOUND, CLEAN_COMPLETION, ORACLE PASS |
| worktree trees equal the hand-made `jinja-before` / `jinja-after` | equal | MISS: not equal (see below) |
| old `--repo` path | unchanged | held (170 old tests pass) |

## The one real surprise: line endings (F-048)
The evaluated worktrees hash equal to an independent reference (`git archive` of the same SHA, extracted, hashed with the same
`tree_hash`): before `dbc9cd7d...`, after `bf8ae6f9...`. They do NOT equal the hand-made checkouts (`jinja-before` `2153ebe4...`,
`jinja-after` `08a0996a...`). The first version of the code gave a CRLF worktree on this machine: the system Git config has
`core.autocrlf=true`, so `git worktree add` converted every text file. The tool now passes `-c core.autocrlf=false` to every git
call it makes, so the evaluated bytes are the bytes of the commit. The most likely reason the hand-made checkouts differ is the same
conversion; I did NOT verify that (I did not diff them). Consequence: Lab #1 results (F-009, F-016, F-047) were obtained on those
hand-made trees; this run shows the same oracle outcome on the exact bytes, but the earlier tree hashes are not the commit's.

## Limits
- Windows only. Linux and Docker are not run here (no Docker on this desktop); a prompt for a Linux session is in
  `LINUX_DOCKER_PROMPT.md`.
- `.gitattributes` `eol` rules still apply in the worktree.
- In host mode the worktree's `.git` file points into the source repository (see PREDICTIONS.md); not mitigated.
- `verify` / replay still takes `--repo`; it has no `--checkout-sha`. Submodules, shallow and sparse clones not covered.
