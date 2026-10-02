# Checkout without `.git` and a writable `/work` (decision_079, F-050, F-051): predictions committed BEFORE the code

Founder decision (decision_079, 2026-10-02): replace `git worktree` by an export of the commit into an empty directory, and
make `/work` writable in Docker mode. Reasons are in `findings.md` F-050 (in host mode a gate-VALID reproducer broke the source
repository through the worktree's `.git` pointer) and F-051 (`/work` is a root-owned 0755 tmpfs, uid 65534 gets EACCES; the
requirement says "/work و /tmp ephemeral writable").

## Design
### 1. Checkout = exact blobs of the commit, no `.git`
- Same CLI (`--checkout-sha`, `--before-sha`, `--after-sha`), same SHA rule (full 40 hex, nothing else), same class
  `reprogate.checkout.Checkout` (`.path`, `.finish()`).
- Mechanism: `git ls-tree -r -z <sha>` lists the tree; `git cat-file --batch` streams every blob; the tool writes the files itself
  into a fresh temp directory outside the evidence bundle. Not `git archive`: it honours `.gitattributes` (`export-ignore`
  would drop files, `export-subst` would rewrite bytes), so it is not "the bytes of the commit". No `core.autocrlf` or other
  conversion is involved because blobs are written as they are.
- Every blob is checked: the tool computes the git object id (`sha1("blob <size>\0" + data)`) and compares it with the id
  from the tree; a mismatch is a `ValueError`. The number of files written must equal the number of blob entries.
- Fail closed (`ValueError`, nothing left behind): a path that is absolute, contains `..`, an empty component or a `.git`
  component; a file that would overwrite another (for example a case-insensitive name collision on Windows); a symlink on
  a platform where it cannot be created (Windows without privilege). On POSIX symlinks are created and the exec bit (mode
  100755) is set. Submodule entries (mode 160000) are not checked out and are counted in the record.
- There is no `.git` file or directory inside the checkout and no worktree is registered in the source repository: the source
  repository is only read (`ls-tree`, `cat-file`, `rev-parse`).
- `environment.json`: `git.commit` is the requested SHA (the tool cannot ask a checkout without `.git`), `dirty_tracked_files`
  is 0 because the files are the verified blobs. `checkout.json`: `mode` `TREE_EXPORT_FROM_SHA`, `requested_sha`,
  `head_sha` (same), `tree_sha` (the commit's tree id), `files_written`, `blobs_verified` (true), `submodules_not_checked_out`,
  `symlinks_created`, `has_git_entry` (false), `source_head_before`, `source_head_after`, `cleanup` (`REMOVED`). The worktree fields
  of F-048 disappear.
- `git worktree` is no longer used anywhere. The F-048 tests that count worktrees change to check that no worktree and no
  `.git` exist.

### 2. `/work` writable in Docker mode
`--tmpfs /work:rw,size=64m,noexec,nosuid,mode=1777` (the same mode as `/tmp`). Nothing else in the container flags changes.
Unit test: the `run_prefix` command contains that exact option (the existing Docker tests skip on Windows; the Linux run of
the old lab measured the real behaviour in F-051).

## Predictions
| item | predicted |
|---|---|
| full SHA, files are exactly the commit's blobs | equal to the blobs byte for byte, including CRLF bytes that were committed, and including files that `.gitattributes` marks `export-ignore` (a unit test commits such a file; `git archive` would drop it, the new checkout must not) |
| hostile or odd tree entries | a tree containing a path with `..` or a `.git` component cannot be built with normal git; the path checks are unit-tested directly on the validator function, which refuses each of: absolute path, `..`, empty component, `.git` component (any case), backslash-drive form |
| refused inputs (abbreviation, branch, tag, HEAD, 39/41 hex, unknown SHA, tree/blob SHA) | unchanged from F-048: `ValueError`, exit 2, nothing created |
| source repository | not written: its `.git` (every file hash), HEAD, refs, `git worktree list` (one entry) and working tree are identical before and after, also when the evaluation raises |
| no way back | in the checkout and in its parent temp directory there is no `.git`; `git -C <checkout> rev-parse` fails (the temp directory is not inside a repository); a reproducer that looks for `.git` walking up from its working directory finds none |
| the F-050 attacks | d2 (create a ref), d3 (delete an object) and d4 (overwrite the branch ref through `os.open`): the paths do not exist; the reproducer fails with an exception; the source `.git` hash is identical afterwards; the real gate's verdict on d4's source is unchanged (VALID) because the defence is the missing target, not the gate |
| evaluated tree vs references | the tree hash of the evaluated checkout of both Lab #1 SHAs equals the F-048 values (before `dbc9cd7d...`, after `bf8ae6f9...`) because jinja has no `export-ignore` at these commits |
| oracle Lab #1 from two SHAs with the real `.venv` as template | ORACLE PASS as in F-048 |
| cost | a few hundred blobs read through one `cat-file --batch` process: well under 5 seconds for jinja (a guess; the measured time is recorded) |
| `/work` | `run_prefix` has `/work:rw,size=64m,noexec,nosuid,mode=1777`; nothing else in the argument list changes (the unit test compares the list with the old one minus that option); the old Docker tests are skipped on Windows |
| old behaviour | `--repo` without `--checkout-sha` unchanged; the existing 179 tests pass except the F-048 worktree-count assertions, which are rewritten (not weakened: they assert more) |
| new tests | in `tests/test_checkout.py` and `tests/test_sandbox.py`; on Windows the symlink and exec-bit tests skip (counted) |

Done when the rows above hold on Windows and a Linux session confirms the Docker and POSIX rows (prompt in
`LINUX_PROMPT.md`). Closing req_005 stays a founder decision.

Not covered: Linux and Docker behaviour (next session), Windows/macOS Docker, `verify`/replay with a SHA, partial/shallow
clones (missing objects fail closed as `ValueError`), SHA-256 object format repositories (the 40-hex rule refuses them), very large
repositories (blobs are read one by one into memory), `.gitattributes` line-ending filters (deliberately not applied),
Git LFS pointers (written as the pointer text, not the large file), whether any real lab reproducer writes to its cwd.
