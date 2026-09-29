# Random sample of bug reports (protocol, fixed before the first draw)

Goal: test ReproGate on bugs that the maintainer did not choose (F-019 lists the selection bias of labs 1-9).

1. Draws are made by `tools/sample_issues.py` with seed `20260929` (two pools: `LIB` and `APP`, see the script header).
   `LIB` = Python libraries in a random 14-day creation window; `APP` = a random repository from the top-30 Python
   `topic:cli` repositories (applications, not libraries), then a random issue.
2. Every draw is recorded in `draws-*.json`, eligible or not. Nothing is redrawn to get an "easier" bug.
3. For each eligible draw the reproducer is written from the issue text only, before looking at the fix.
   The fix commit is the one found by rule E2 (see Amendment 1); the affected commit is its first parent.
4. Before any reproducer is executed, `expected_outcomes.json` (the prediction) is committed for each lab.
5. Draws that cannot be evaluated (no reproducer possible from the text, dependencies cannot be installed, ...) stay in
   the table with the reason. A failed prediction is reported, not hidden, and can lead to a finding.
6. Limits stated up front: only exception claims are supported, so the E1 filter (traceback in the body) already
   excludes wrong-output bugs; the sample is small and is not a benchmark.

## Amendment 1 (E2 eligibility rule)

Reason: with the original E2 (the issue's `closed` event carries a commit) 0 of 18 draws were eligible in v1
(`draws-lib-v1-strict-E2.json`, `draws-app-v1-strict-E2.json`, kept unchanged). This is a structural defect of that
E2 rule: an issue closed by merging a pull request usually has no commit on its `closed` event, so a fix commit
existed but the rule could not see it. At the time of the amendment no lab or reproducer for the sample had been
written or run. E2 now also accepts a merged PR of the same repository that cross-references the issue (its merge
commit is the fix). The same seed is used, so the sequence of drawn issues is the same; only the eligibility test changed.

## Stopping rules (fixed before the v2 draw)

- The v2 draw is executed exactly once per pool. Its first result is the sample; it is not re-run, and the seed,
  pool definitions and search queries are not changed afterwards.
- The number of labs per pool is fixed in advance: the first 3 eligible draws of `LIB` and the first 2 eligible
  draws of `APP` (at most 10 and 8 draws respectively). If fewer are eligible, the sample is smaller; it is not extended.
- An eligible draw whose reproducer cannot be written from the issue text is not dropped: it is recorded as
  `NOT_EVALUATED` with the reason and counts in the totals.
- No prediction, reproducer or claim is edited after its first run to make it pass; a mismatch is reported as a
  mismatch (and may become a finding).
