# `wrong_output` pilot on real bugs: results of the candidate search (2026-10-01)

Protocol: `PROTOCOL.md`, commit 435b219 (written before the first search). All rows and reasons: `CANDIDATES.md`.

## What happened

30 candidates were examined in the order fixed by the protocol. **None was evaluable.** No claim was written, no reproducer
was written and the tool was not run on any real bug, because the first step of the method (an evaluable candidate) was
never reached. No result label of the protocol (`TOOL_AGREES`, `TOOL_DISAGREES`, `CLAIM_NOT_EXTRACTABLE`, `ENV_FAILED`) applies.

| failed first on | count |
|---|---|
| condition 1: no stated call with an expected and an actual value that are Python literals (mostly exceptions) | 22 |
| condition 3: needs a network service, an AWS account or sockets | 6 |
| condition 2: no merged fix with a regression test in the same repository | 2 |
| evaluable | 0 |

## What this does and does not show

- With this selection (popular packages in download-rank order, the oldest closed issue containing "expected" and
  "actual" or "got"), bugs of the form "a function returns a wrong value and the issue states both values" were not found
  in 30 candidates. The search matches the words, not the bug shape; most hits were exceptions.
- It does not show that such bugs are rare in general, and it says nothing about the accuracy of `wrong_output`. Candidates
  are in download-rank order, five rows were judged from the title alone, and the reading of "literal" is the
  maintainer's.
- The mechanism itself (F-039, F-040) is untouched: it still works on the synthetic cases and was never tried on a real one.

## Not done, on purpose

The sample was not extended past 30 and the method was not changed after seeing the result. A second pilot with a
different selection (for example starting from merged fixes that add an assertion on a returned value) is possible, but
it needs its own protocol committed first and a separate decision; it is not part of this one.
