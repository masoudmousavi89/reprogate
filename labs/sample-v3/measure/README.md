# Blind-session reproducers (archive, not M1/M2 data)

**Status: not labelled. These 18 scripts are not M1/M2 data, and no result is derived from them.** Human labelling was
stopped because no independent programmer is available to label (maintainer decision, 2026-09-29). M1/M2 for the NARROW
sample stays INCONCLUSIVE (n = 6 < 10, `STOP_CRITERIA.md`). The scripts are kept as evidence and as material for a later
labeller or a later round.

Protocol: `../MEASUREMENT-PROTOCOL.md` (a633d06). Deviations: `../DEVIATIONS.md`.

## Provenance

- Blind environment: a separate private repository, `bug-repro-sandbox`, holding only `ISSUES.md` and `PROMPT.md` (the
  files of `../blind-input/`, sha256 as recorded in the protocol). During the three sessions the GitHub App of the cloud
  sessions had access to that repository only.
- Three new cloud sessions, one per attempt, same task text, model Sonnet 5.5. Each pushed its own branch:
  attempt 1 `0a1ecf5`, attempt 2 `0b17f13`, attempt 3 `d92faf6` (commits of `bug-repro-sandbox`). The sessions shared no
  memory and did not see each other's branches.
- Layout: `n-XX/attempt-K/repro.py`, `run.txt` (stdout, stderr and exit code of the final run), `notes.md` (command,
  Python version, PYTHONPATH). Copied unchanged except for the path masking below.

## Path masking (run.txt and notes.md only; repro.py files are byte-identical to the blind repository)

| original | replaced by |
|---|---|
| `/tmp/<tool>-0/-home-user-bug-repro-sandbox` (tool name elided here) | `<SCRATCH>` |
| `/home/user/bug-repro-sandbox` | `<WORK>` |
| `/root/` | `<HOME>/` |

Paths inside the bug reporters' own tracebacks (in `../blind-input/ISSUES.md`) are public report text and are not changed.
