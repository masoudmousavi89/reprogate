# Checkout without `.git` and writable `/work`: results (Windows, py -3.8.10, 2026-10-02)

Predictions: `PREDICTIONS.md`, committed first as b4b508b. Code and tests: 5d33f9c. Runner: `labs/checkout-sha/run_checkout_sha.ps1`
(unchanged, it already prints what is needed), log `run-windows-2026-10-02.log`. This replaces the worktree mechanism of F-048 /
`labs/checkout-sha/` (that lab stays as history).

## Tests
184 tests OK, 12 skipped (before: 179 OK, 11 skipped). `tests/test_checkout.py` now has 13 tests (the 9 of F-048 are rewritten to the
new mechanism and assert more; one POSIX-only test, exec bit and symlink, is the extra skip on Windows) and
`tests/test_sandbox.py` has one new test for the `/work` option. Also run with `-W error::ResourceWarning`: clean after one fix
(the `cat-file` pipe was not closed; fixed before the commit).

## Predictions vs observed
| item | predicted | observed |
|---|---|---|
| exact blobs, including `export-ignore` files, not the working tree | equal to the blobs | held (unit test: a file marked `export-ignore` is exported; bytes equal `git cat-file blob`; `eol=crlf` in `.gitattributes` is NOT applied) |
| path validator | refuses absolute, `..`, empty component, `.git` component (any case), backslash and drive forms | held (unit test over 15 bad inputs and 5 good ones) |
| refused inputs | unchanged from F-048 | held (unit tests; CLI abbreviation and `master` give exit 2) |
| source repository not written | `.git` hash, HEAD, refs, worktree list, working tree identical, also when the evaluation raises | held (unit tests hash every file under the source `.git`; the Lab #1 run: source head and tree unchanged, one worktree before and after) |
| no way back | no `.git` in the checkout or its parent; `git rev-parse` fails inside it; a reproducer walking up for `.git` finds none | held (unit tests; the walking reproducer completes in 3 of 3 runs) |
| tampered object | (not predicted in detail) | a damaged loose object stops the export with `ValueError`, nothing left behind |
| the F-050 attacks (d2, d3, d4) | nothing to write to | by construction and by the walk-up test; the attacks themselves were NOT re-run (they need Linux and a throwaway repository); a Linux run is the confirmation (`LINUX_PROMPT.md`) |
| tree hashes of Lab #1 vs F-048 | `dbc9cd7d...` and `bf8ae6f9...` | held: identical, 126 files each, equal to the independent `git archive` references |
| oracle Lab #1 from two SHAs, real `.venv` as template | ORACLE PASS | held |
| cost | well under 5 seconds | held: 1.0 s and 1.6 s for the two jinja commits (126 blobs each) |
| `/work` | only the tmpfs option changes | held (unit test: option present with `mode=1777`, `/tmp` unchanged, two tmpfs options); real behaviour in Docker is NOT measured here |
| old behaviour | `--repo` unchanged | held |

No prediction was missed. One wording point: I predicted the F-048 tests that count worktrees would be "rewritten, not weakened"; they now
also hash the whole source `.git`.

## Limits
- Windows only. The Docker `/work` fix and the POSIX parts (exec bit, symlinks) are untested on a real system; a Linux session is needed
  (`LINUX_PROMPT.md`).
- Submodules are counted and not checked out; symlinks fail closed on Windows; partial or shallow clones fail closed; SHA-256 repositories
  are refused by the 40-hex rule; Git LFS pointers are written as pointer text.
- Blobs are read one by one into memory (large files and very large repositories not tried).
- `verify` / replay still takes `--repo` and has no `--checkout-sha`.
- `environment.json` records the SHA as `git.commit`; because a checkout without `.git` cannot be asked, that value is the requested SHA
  after every blob was checked against its object id.
