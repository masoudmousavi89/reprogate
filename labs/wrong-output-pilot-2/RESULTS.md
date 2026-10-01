# `wrong_output` pilot 2 on real bugs: results of the candidate search (2026-10-01)

Protocol: `PROTOCOL.md`, commit 01a327e (written before the first search). All rows and reasons: `CANDIDATES.md`.

## What happened

40 pull requests were examined in the order fixed by the protocol (after the correction described below). **None was
evaluable.** No claim was written, no reproducer was written and the tool was not run on any real bug, because the first
step of the method (an evaluable candidate) was never reached. No result label of the protocol applies.

| failed first on | count |
|---|---|
| the file screen (no assertion on a returned value compared with a literal added to a test) | 24 |
| condition 1 (no stated call with expected and actual values that are Python literals) | 12 |
| condition 1 and 3 | 1 |
| condition 3 (needs a network service or an S3 service) | 2 |
| condition 2 (no fix with a regression test of the issue's call in the same repository) | 1 |
| evaluable | 0 |

Two near misses, both on a technicality of the claim format, not on the bug: pyasn1 issue #81 (`asDateTime` returns the wrong value and
both values are stated, but they are `datetime` objects, not Python literals), and the mdurl fix for markdown-it-py issue #222
(a function returns a wrong string and both strings are stated, but the issue is in another repository and names a call that the
regression test does not make).

## The screening mistake and what it showed

The first screening run did not apply the exclusion of pilot 1's named repositories correctly (see `CANDIDATES.md`). Before
the correction it had examined 21 pull requests of excluded repositories, among them python-pathspec. Reading that run,
one candidate would have been evaluable by the four conditions: `cpburnz/python-pathspec` issue #129 (`GitIgnoreSpec.from_lines(["build", "!keep.log"]).match_file("build/keep.log")`
returns False, expected True), fixed by pull request #132 with a regression test, pure Python with no runtime dependencies,
but it needs Python 3.9 (`requires-python >=3.9`), which is not installed on the Windows machine. It was **not** part of this
pilot and was not run: it was excluded by the protocol, and keeping a candidate because it looked good after the fact is what the
pre-registration exists to prevent. It is recorded here as an observation about the method (a single suitable bug exists among
the repositories first examined) and as an open question: whether to test it as a separate, pre-registered single case.

## What this does and does not show

- Choosing from the fix side did not produce an evaluable candidate in 40 pull requests either. Together with pilot 1 (30 issues,
  0 evaluable) the practicality of `wrong_output` on real bugs is still **unanswered**, not answered negatively: the tool was never run on
  a real bug.
- The claim format needs the target function to return a Python literal (numbers, strings, containers, booleans, None). Many real
  wrong-value bugs return other objects (datetime, custom classes); this is a limit of the claim format, not of those bugs.
- Newest-first and download-rank order bias the sample (stated in the protocol); five rows in pilot 1 and three here were judged
  from part of the issue text.

## Not done, on purpose

The sample was not extended past 40 and the method was not changed after seeing the result. Any further pilot or a single case
run needs its own protocol committed first and a separate decision.
