# Lab #1 (pallets/jinja#843) - Windows run guide

This lab does **not** need Docker. It needs only Python 3.8 and the two
checkout folders you prepared yourself (`jinja-before` and `jinja-after`, with
`.venv` and `.venv-unpinned`).

## Step 1: extract the archive
Extract the zip, for example into `C:\path\to\reprogate-lab\`, then open
PowerShell in the extracted folder (the one containing `README.md` and the
`reprogate` package):

```
cd C:\path\to\reprogate-lab\reprogate-py-prototype
```

## Step 2: run the project's own tests on Python 3.8
```
py -3.8 -m unittest discover -s tests -t . -v
```
Expected: `Ran 43 tests` and `OK` (roughly 30 to 60 seconds).
If anything fails, keep the **full output**; that is finding F-007 (Python 3.8
compatibility).

## Step 3: the real experiment
```
powershell -ExecutionPolicy Bypass -File labs\jinja-843\run_lab001.ps1
```
- The script warns that there is no sandbox. It only runs the short files
  `repro.py` and `fixtures\*.py` (you can read them first). Nothing is installed.
- If asked, type `YES`.
- With network access it fetches the raw issue body from GitHub and checks
  provenance **mechanically**. Without network it continues and records in the
  evidence that provenance was unverified.

## Step 4: what to record
1. The output of step 2 (the last few lines are enough, unless it failed).
2. The final table of step 3 (`results.md`): columns expected / actual / ok.
3. The full text of any error you see.

## Expected outcomes (written before the run)
| Case | Expected |
|---|---|
| oracle: before fix | `SYMPTOM_REPRODUCED` |
| oracle: after fix | clean completion (`CLEAN_COMPLETION`) |
| MarkupSafe not pinned | `NOT_EVALUATED / ENVIRONMENT_UNAVAILABLE` |
| f01 (direct raise) | `NOT_EVALUATED / REPRODUCER_REJECTED` |
| f02 (direct `deque().popleft()`) | `NO_MATCHING_REPRODUCTION_FOUND` |
| f03 (fake traceback on stdout) | `NO_MATCHING_REPRODUCTION_FOUND` |
| f04 (subclass with override) | `NO_MATCHING_REPRODUCTION_FOUND` |

If a row does not match the expectation, that is fine: **it is a real finding**
and is recorded in `findings.md`.
