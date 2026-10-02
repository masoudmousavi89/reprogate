# Fresh checkout of an exact SHA (req_005): predictions and design committed BEFORE the code

Requirement text (req_005, one of its explicit clauses): "fresh checkout exact SHA". State before this change, read from the
code: `run` and `oracle` take `--repo` / `--before-repo` / `--after-repo`, an existing directory prepared by hand. The tool records
`git rev-parse HEAD` of that directory and the count of dirty tracked files, but never creates the checkout, so nothing in the
tool guarantees that the evaluated tree is exactly the commit named in the claim (`target.affected_commit`, `fix_commit`).
Docker is not available on this desktop; the Docker part of req_005 stays as evidence F-017 (Linux) and is not touched here.

## Design (founder preference: `git worktree`, provided the isolation the tool needs is kept)
- New options: `run --checkout-sha SHA` (then `--repo` is the SOURCE repository) and `oracle --before-sha SHA --after-sha SHA`
  (then `--before-repo` / `--after-repo` are source repositories; they may be the same repository).
- SHA rule: exactly 40 hexadecimal characters (either case, stored lowercase). Abbreviations, branch names, tags, `HEAD` and
  revision expressions are refused with `ValueError` (exit code 2) before anything is created, because a name can move.
  The object must exist in the source repository and must be a commit.
- Mechanism: `git worktree add --detach <fresh temp dir outside the evidence bundle> <sha>`; the tool then checks that
  `git rev-parse HEAD` in the worktree equals the SHA and that `git status --porcelain` is empty. Any mismatch is a
  `ValueError`. The evaluation runs on the worktree; afterwards the worktree is removed (`git worktree remove --force`, then
  `git worktree prune`), also when the evaluation raises.
- Recorded in `environment.json` under `checkout`: `mode` (`WORKTREE_DETACHED_FROM_SHA`), `requested_sha`, `head_sha`, `clean`
  and, for the source repository, `source_head_before` / `source_head_after` and `cleanup` (`REMOVED`). The existing
  `repository_tree_sha256_before` and the REPOSITORY_MODIFIED rule apply to the worktree unchanged.
- Without the new option nothing changes (the old path with an existing directory still works and is still labelled as before).
- Isolation: a worktree shares the source repository's `.git` (its `.git` is a file pointing into it). In host mode a
  reproducer that writes outside the checkout is already out of scope (THREAT_MODEL, no sandbox; the static gate rejects file
  and process operations as a first line). So host mode gets a new, small exposure: the source repository's `.git` is
  reachable from the checkout. This change does NOT mitigate it; it only records the source HEAD before and after. In Docker
  mode `/repo` is mounted read-only and the gitdir path of the host is not mounted, so the pointer leads nowhere (reasoned
  from F-017, NOT tested here: no Docker on this machine). A fully isolated alternative (`git archive` into an empty directory,
  no `.git` at all) exists and is not used because of the founder's preference; it is the fallback if a test below fails.

## Predictions
| item | predicted |
|---|---|
| full SHA of an existing commit | worktree HEAD equals the SHA, `status` clean; its files are those of that commit even when the source working tree is at another commit, has uncommitted edits or untracked files |
| abbreviated SHA, branch name, tag, `HEAD`, 39 or 41 hex, non-hex | `ValueError`, exit 2, no worktree created, `git worktree list` of the source unchanged |
| well-formed SHA that does not exist; SHA of a tree or a blob | `ValueError`, exit 2, nothing left behind |
| cleanup | after the call the temp directory is gone and `git worktree list` of the source has only the main entry, also when the evaluation raises; source HEAD and source tree hash unchanged |
| `environment.json` | has `checkout` with the fields above; `git.commit` equals the requested SHA; `repository_tree_sha256_before` equals the tree hash of the same commit taken from an independent checkout |
| reproducer that edits a tracked file of the checkout | run status REPOSITORY_MODIFIED as today; the source working tree is not changed |
| Lab #1 oracle with `--before-sha 81825095d24f4dbccb40f787fff70db54989b91c --after-sha 9a7dd7b28b50fd8adc019ab2702b50ae5c6ed782` on the jinja clone in `~/reprogate-lab/jinja` and the wheelhouse template of F-047 | ORACLE PASS as in F-047; the tree hashes of the two worktrees equal the tree hashes of the hand-made `jinja-before` and `jinja-after` checkouts (so the evaluated trees are the same bytes as in F-009/F-016/F-047) |
| old `--repo` path without the new option | unchanged: the existing test suite (170 tests, 11 skipped on Windows) passes |
| new tests | `tests/test_checkout.py` covers the rows above that need no real project (a throwaway git repository with two commits) |

Done for the checkout clause of req_005 if the rows above hold on Windows. req_005 as a whole stays open for what this does
not show (below); closing it is a founder decision.

Not covered: Docker on this desktop (and Windows/macOS Docker at all), `verify` / replay with `--checkout-sha` (replay still
takes `--repo`), submodules, shallow or partial clones, sparse checkout, repositories where `git worktree` is unavailable,
Linux for this change (not run), the host-mode exposure of the source `.git` described above.
