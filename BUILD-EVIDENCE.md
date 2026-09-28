# Build evidence - 2026-09-20

Verified in the build sandbox (Linux, no network, no Docker, no PowerShell):

- Python 3.12.3.
- 43 tests pass (`python -m unittest discover -s tests -t .`), also from a clean extraction of the zip,
  with ResourceWarnings promoted to errors.
- All modules under `reprogate/` and `tools/` parse with the Python 3.8 grammar
  (`ast.parse(..., feature_version=(3, 8))`) and contain none of a short list of 3.9+ APIs.
- The CLI flow `claim-check -> run -> oracle -> inspect -> verify` works on a synthetic library, and
  `run` refuses to execute without `--allow-host-execution`.
- The static gate gives the expected statuses on the lab reproducer (VALID), fixture f01 (REJECTED) and
  fixtures f02-f04 (VALID, caught later by the runtime origin check).

Verified later, 2026-09-29 (Windows 11, Python 3.8.10): the full suite (43 tests) passes under `py -3.8`.

NOT verified (these remain validation gates, not achievements):

- Any run of the real Jinja lab (see below for what was verified on Python 3.8).
- Any run on Windows, and `labs/jinja-843/run_lab001.ps1` itself (never executed).
- Any run against the real Jinja checkouts, the real MarkupSafe pin, or the real GitHub API
  (`tools/fetch_issue.py` and `claim-check` on the raw issue body).
- Docker or any sandbox (does not exist in this prototype).
- Whether the authenticity check (bytecode comparison) has false negatives on real Jinja frames.
