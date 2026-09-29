# Task (the same text is used for each of the three sessions; only ATTEMPT changes)

ATTEMPT = <1, 2 or 3>

This repository contains `ISSUES.md`: six bug reports from open-source Python projects. For each report it gives the
repository and the exact commit where the bug is present.

For each of the six bugs, write one standalone Python script that triggers the exception described in the report when
it is run against the project code at that commit.

Rules:
1. Work only from the report text in `ISSUES.md` and the project code at the given commit. Get the code with
   `git init <dir> && git -C <dir> fetch --depth 1 <repository URL> <commit> && git -C <dir> checkout FETCH_HEAD`.
   Do not fetch any other history, branch, tag or pull request, and do not open the issue page or any other web page
   about the bug.
2. You may create a virtual environment, install the dependencies the project declares, and run your script as often
   as you like. Do not change the project files. The script must not contact external network services.
3. Make the project importable by putting its checkout (or its `src/` folder) on `PYTHONPATH`; do not install it.
4. Write the script as `<bug id>/attempt-<ATTEMPT>/repro.py` (bug ids as in `ISSUES.md`, for example `n-23`).
5. Run it once more at the end with the command you used, and save the complete stdout, stderr and exit code in
   `<bug id>/attempt-<ATTEMPT>/run.txt`. In `<bug id>/attempt-<ATTEMPT>/notes.md` write the command, the Python
   version and the PYTHONPATH (two or three lines, no other explanation).
6. If you cannot trigger the exception, still save your best script and its run, and say so in one line in notes.md.
7. Do not look at other attempt folders. Commit all files and push.
