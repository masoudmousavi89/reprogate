# Linux verification run 2 (F-032..F-036): predictions committed BEFORE the run

Linux container, CPython 3.8 (uv), Docker, image mirror.gcr.io/library/python:3.8-slim; more-itertools-falsy on 3.12.
Windows reference: 136 tests OK (11 skipped: 5 POSIX-only, 6 Docker); labs 2-9 29 of 29 rows; jinja-843 6 of 6.

A. Unit tests (python3.8 -m unittest discover -s tests -t .): 136 run, 0 failures, 0 errors, 0 skipped (POSIX and Docker
   tests run here).
B. F-032 fresh environment on Linux host mode (run_fresh_env.sh, port of run_fresh_env.ps1; Lab #1 pair, MarkupSafe==2.0.1):
   d01 NO_MATCHING_REPRODUCTION_FOUND/NONE with 5 COMPLETED, template file hash unchanged, recorded mode FRESH_COPY_PER_RUN,
   recorded template hash equal to an independent tree hash; d01 again: same template hash and outcome; d02 marker length 0;
   d03 5 COMPLETED and 5 clean completions; template tree hash unchanged after all attacks; jinja oracle with the real .venv
   as read-only template: ORACLE PASS, 2 of 2 bundles invariants OK, real .venv tree hash unchanged. The venv symlinks
   (bin/python -> system interpreter, lib64 -> lib) are copied as links and do not make a run write into the template.
C. jinja-843 (run_lab001.sh): 6 of 6 rows as in expected_outcomes.json.
D. Labs 2-9 host mode (tools/run_lab.py): 33 of 33 rows as in each expected_outcomes.json (29 rows on 3.8 in 7 labs,
   4 rows of more-itertools-falsy on 3.12). sortedcontainers-eq oracle PASS with LOCATION_VIA_NESTED_SCOPE in the
   "before" runs (F-034).
E. Docker: sortedcontainers-eq oracle with --sandbox docker: before SYMPTOM_REPRODUCED with LOCATION_VIA_NESTED_SCOPE,
   ORACLE PASS (F-033/F-034 with /repo paths inside the container).
F. F-035/F-036 on Linux: labs/incomplete-bundle/cases.py and labs/bundle-structure/cases.py print the same 30 lines as the
   "after" columns of their RESULTS.md (b01-b05, b10-b13, b15 exit 2 INVALID_BUNDLE; b06, b09, b14 exit 1; b07, b08 exit 0;
   h01-h03, h08-h15 exit 1; h04-h07 exit 2 INVALID_BUNDLE). inspect exit 0 with invariants OK and hashes OK on every
   bundle produced in B-E; verify PASS (exit 0, no STRUCTURE line) on the jinja oracle "before" bundle in host mode and on
   the Docker sortedcontainers-eq oracle "before" bundle with --sandbox docker.
