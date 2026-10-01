# `wrong_output` pilot 2 on real bugs: protocol fixed before any search or run

Status: pre-registered 2026-10-01, before a single candidate is searched or run. It follows pilot 1
(`labs/wrong-output-pilot/`, result: 30 candidates, 0 evaluable, F-041). `wrong_output` stays EXPERIMENTAL. No accuracy,
reliability or coverage figure comes out of this pilot.

## Question

Is the `wrong_output` path practical on real bugs when candidates are chosen from the fix side (a merged pull request
that adds a test asserting a returned value) instead of from the words of an issue? It does not measure accuracy.

## What this pilot is not

- Not an accuracy measurement and not a benchmark. At most 5 evaluable bugs.
- No success threshold. Counts and every row are reported; whether the result is good or bad is decided afterwards in a
  separate dated decision, never by editing this file.
- The answer key is not independent of the project (see "Limits").

## Candidate selection (fixed here, applied in this order, no random draw)

1. Pool: `labs/sample-v3/narrow-packages.json` in ascending `rank`.
2. Excluded: the repositories in `labs/sample-v3/excluded-repos.json`, every repository in `labs/sample-v3/draws-*.json`,
   and every repository that appears in `labs/wrong-output-pilot/CANDIDATES.md` (pilot 1).
3. For each package in order, one search on its repository: merged pull requests that are linked to an issue
   (`is:pr is:merged linked:issue`), newest first. Examine at most the first 3 results per package; a package with no
   result is skipped, and a repository that cannot be searched (HTTP 422) is skipped and listed.
4. For each pull request, read its list of changed files (one API call). It passes the screen only if it adds, in a test
   file, an assertion on a returned value compared with a literal (for example `assert f(x) == 3` or
   `assertEqual(f(x), "a")`). Then the issue it links is read for the evaluability conditions below.
5. Stop when 5 candidates are evaluable or after 40 pull requests have been examined, whichever comes first. The
   sample is not extended.
6. Every pull request examined is listed with its verdict, including the rejected ones, in `CANDIDATES.md`.

## Evaluable (all four required, decided by reading before any run)

1. The linked issue states a call (or input) and an expected and an actual value that can be written as Python literals.
2. The merged pull request fixes it and adds or changes a regression test that exercises that call (given by the
   selection, still checked by reading).
3. No network service, GUI, special hardware or unsafe input is needed.
4. The project can be installed by the method of `labs/sample-v3/INSTALL-CHECK.md` (wheels only, project checkout on
   PYTHONPATH, Python 3.8 or the lowest declared version >= 3.8).

A candidate that fails a condition is NOT_EVALUATED with the number of the condition, and stays in the list.

## Method for each evaluable bug, in this order

1. Write the claim (`kind: wrong_output`) from the issue text only, before opening the code. Run `claim-check` on the raw
   issue body (`tools/fetch_issue.py`). Freeze it. The claim is never edited afterwards.
2. Commit a prediction (what the tool should output for each reproducer) before the first run.
3. Write the reproducer from the issue text (the call or snippet the issue gives, adapted to a plain script). Record the
   origin (`ISSUE_VERBATIM_SNIPPET` or `AGENT_ADAPTED`) with the diff.
4. Answer key: run the regression test that the fix added, on the affected commit (first parent of the merge or the
   base of the pull request) and on the fix. Expected: fails before, passes after. If not, the bug is NOT_EVALUATED
   (condition 2) and no verdict is recorded.
5. Run the tool: `oracle` with the frozen claim and the reproducer, 5 runs per commit, Windows host mode first.
6. Compare the tool's outcome with the answer key. Neither side is changed after seeing the other.

## Result labels (one per bug, no others)

- `TOOL_AGREES`: oracle PASS and the answer key fails before and passes after.
- `TOOL_DISAGREES`: any other combination where the claim and environment were fine; recorded as a finding.
- `CLAIM_NOT_EXTRACTABLE`: the four parts could not be written as literals from the issue text (a result, not a failure to hide).
- `ENV_FAILED`: the environment could not be built or the interpreter failed before the claim could be judged.

## Report

A table with one row per examined pull request, counts per label, and a `findings.md` entry for every
`TOOL_DISAGREES` or `CLAIM_NOT_EXTRACTABLE`. No percentage is stated.

## Limits (stated before the run)

- Choosing from the fix side favours bugs that are easy to test with an assertion on a returned value, so the result is
  more favourable than the population of real bugs. This is a different bias from pilot 1, not a smaller one.
- Newest-first favours active projects and recent versions.
- Candidates follow download rank, so popular, well-tested projects are over-represented.
- The answer key is the maintainers' own regression test, written with knowledge of the fix; agreement does not make
  the tool independent of the project.
- The reproducers are written from the issue text by an AI assistant (as in the blind sessions).
- At most 5 evaluable bugs: this shows whether the path is practical, nothing about accuracy or generalisation.
- A reproducer that imitates the observation protocol (w09, b05) is still accepted; the pilot does not test that.
- Windows host mode only in the first pass; a Linux/Docker pass follows with its own predictions committed first.
