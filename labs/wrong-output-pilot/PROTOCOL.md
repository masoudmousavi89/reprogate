# `wrong_output` pilot on real bugs: protocol, fixed before any search or run

Status: pre-registered 2026-10-01, before a single candidate is searched or run. Decision: `wrong_output` stays
EXPERIMENTAL. No accuracy, reliability or coverage figure comes out of this pilot.

## Question

Is the `wrong_output` path practical on real bugs: can the four-part claim (target function, input, expected, actual) be
taken from a real issue, and does the verdict agree with the project's own fix and its regression test? It does not
measure how accurate the tool is.

## What this pilot is not

- Not an accuracy measurement and not a benchmark. At most 5 bugs.
- No success threshold. Counts and every row are reported; whether the result is good or bad is decided afterwards, in a
  separate dated decision, never by moving a line in this file.
- The answer key (below) is not independent of the project; see "Limits".

## Candidate selection (fixed here, applied in this order, no random draw)

1. Pool: `labs/sample-v3/narrow-packages.json` (759 packages with a py3-none-any wheel and a GitHub repository), in
   ascending `rank`.
2. Excluded: the repositories in `labs/sample-v3/excluded-repos.json` (labs 1-9 and the v2 draws) and every repository
   that appears in `labs/sample-v3/draws-narrow.json`, `draws-wide-lib.json` or `draws-wide-app.json`.
3. For each package in order, one search on its repository: closed issues whose body contains both the word `expected`
   and (`actual` or `got`) in the GitHub issue search; take the oldest result. A package without a result is skipped.
4. Stop when 5 candidates are evaluable or after 30 candidates examined, whichever comes first. The sample is not extended.
5. Every candidate examined is listed with its verdict, including the rejected ones, in `CANDIDATES.md`.

## Evaluable (all four required, decided by reading before any run)

1. The issue states a call (or input) and an expected and an actual value that can be written as Python literals.
2. A merged pull request fixes it and adds or changes a regression test that exercises that call.
3. No network service, GUI, special hardware or unsafe input is needed.
4. The project can be installed by the method of `labs/sample-v3/INSTALL-CHECK.md` (wheels only, project checkout on
   PYTHONPATH, Python 3.8 or the lowest declared version >= 3.8).

A candidate that fails a condition is NOT_EVALUATED with the number of the condition, and stays in the list.

## Method for each evaluable bug, in this order

1. Write the claim (`kind: wrong_output`) from the issue text only, before opening the code. Run `claim-check` on the raw
   issue body (`tools/fetch_issue.py`). Freeze it. The claim is never edited afterwards.
2. Commit a prediction (what the tool should output for each reproducer below) before the first run.
3. Write the reproducer from the issue text (the call or snippet the issue gives, adapted to a plain script). Record the
   origin (`ISSUE_VERBATIM_SNIPPET` or `AGENT_ADAPTED`) with the diff.
4. Answer key: run the regression test that the fix added, on the affected commit (first parent of the fix) and on the
   fix. Expected: it fails before and passes after. If it does not, the bug is NOT_EVALUATED (condition 2) and no
   verdict is recorded.
5. Run the tool: `oracle` with the frozen claim and the reproducer, 5 runs per commit, Windows host mode first.
6. Compare the tool's outcome with the answer key. Neither side is changed after seeing the other.

## Result labels (one per bug, no others)

- `TOOL_AGREES`: oracle PASS and the answer key fails before and passes after.
- `TOOL_DISAGREES`: any other combination where the claim and environment were fine. The details are recorded as a finding.
- `CLAIM_NOT_EXTRACTABLE`: the four parts could not be written as literals from the issue text (this is a result, not a
  failure to hide).
- `ENV_FAILED`: the environment could not be built or the interpreter failed before the claim could be judged.

## Report

A table with one row per examined candidate, counts per label, and the findings that `TOOL_DISAGREES` or
`CLAIM_NOT_EXTRACTABLE` produce (each with a `findings.md` entry under the project rule). No percentage is stated.

## Limits (stated before the run)

- Candidates are taken in download-rank order, so popular, well-tested projects are over-represented.
- The answer key is the maintainers' own regression test. A test can be narrower or broader than the reported bug, and
  it was written with knowledge of the fix, so agreement does not make the tool independent of the project.
- The reproducers are written from the issue text by an AI assistant (as in the blind sessions), not by independent
  programmers.
- At most 5 evaluable bugs: this shows whether the path is practical, nothing about accuracy or generalisation.
- A reproducer that imitates the observation protocol (w09, b05) is still accepted by the tool; the pilot does not test that.
- Windows host mode only in the first pass; a Linux/Docker pass follows with its own predictions committed first.
