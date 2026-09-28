# findings.md

Rule: architecture changes only with a finding that cites evidence. IDs are permanent.

| id | date | status | finding | evidence | consequence |
|---|---|---|---|---|---|
| F-001 | 2026-09-20 | confirmed | Traceback line numbers differ from the issue (issue: 424, real run: 417). | manual smoke test on the pre-fix commit | anchors must not contain line numbers (implemented: file + function only) |
| F-002 | 2026-09-20 | confirmed | On Windows the traceback path is absolute with backslashes; the issue shows a relative forward-slash path. | manual smoke test | location is compared as repo-relative, normalised path (implemented in matcher/harness) |
| F-003 | 2026-09-20 | confirmed | The real symptom (IndexError) and an environment failure (ImportError) both exit with code 1. | manual runs pinned vs unpinned MarkupSafe | exit code is never used; structured observation only |
| F-004 | 2026-09-20 | confirmed | The ImportError traceback also contains repository frames (jinja2\utils.py, line 669), so "a repo frame is present" is not enough. | manual run without the pin | type/message must match the claim; import-phase failures classify as ENV_FAILURE |
| F-005 | 2026-09-20 | confirmed | MarkupSafe==2.0.1 works, 2.1.5 fails at import for this commit (pin needed; the exact boundary is untested). | manual runs | environment must be part of the evidence (environment.json records packages) |
| F-006 | 2026-09-20 | OPEN | A previously frozen issue snapshot may be a reconstruction (its build environment had no GitHub access). Spans/hashes on rendered text are not spans on the raw body. | project changelog, not inspectable here | re-snapshot with tools/fetch_issue.py and re-run claim-check; mark old one RECONSTRUCTED |
| F-007 | 2026-09-29 | closed | The earlier observer was only tested on Python 3.13, but the target interpreter is 3.8. This prototype's grammar is checked against 3.8 but has not been run on 3.8. | BUILD-EVIDENCE.md; tests/test_py38_compat.py | closed: `py -3.8 -m unittest discover -s tests -t .` on Python 3.8.10 / Windows 11 ran 43 tests, all OK (2026-09-29) |
| F-008 | 2026-09-20 | confirmed | The reproducer hash depends on line endings (PowerShell wrote CRLF). | manual hash 1E688F1A... vs LF file | record reproducer bytes exactly as executed; do not normalise silently |
