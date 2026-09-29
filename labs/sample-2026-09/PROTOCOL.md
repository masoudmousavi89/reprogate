# Random sample of bug reports (protocol, fixed before the first draw)

Goal: test ReproGate on bugs that the maintainer did not choose (F-019 lists the selection bias of labs 1-9).

1. Draws are made by `tools/sample_issues.py` with seed `20260929` (two pools: `LIB` and `APP`, see the script header).
   `LIB` = Python libraries in a random 14-day creation window; `APP` = a random repository from the top-30 Python
   `topic:cli` repositories (applications, not libraries), then a random issue.
2. Every draw is recorded in `draws.json`, eligible or not. Nothing is redrawn to get an "easier" bug.
3. For each eligible draw the reproducer is written from the issue text only, before looking at the fix.
   The affected commit is the parent of the commit referenced by the issue's `closed` event; the fix commit is that commit.
4. Before any reproducer is executed, `expected_outcomes.json` (the prediction) is committed for each lab.
5. Draws that cannot be evaluated (no reproducer possible from the text, dependencies cannot be installed, ...) stay in
   the table with the reason. A failed prediction is reported, not hidden, and can lead to a finding.
6. Limits stated up front: only exception claims are supported, so the E1 filter (traceback in the body) already
   excludes wrong-output bugs; the sample is small and is not a benchmark.
