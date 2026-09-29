# Sample v3, WIDE pool: evaluability checklist and M4 (2026-09-29)

Protocol: `PROTOCOL.md` (9642a0d). Draws: `draws-wide-lib.json`, `draws-wide-app.json` (e0e5343). Condition 4 for the
candidates: `INSTALL-CHECK.md` (7f1ffa6 method and predictions, 869ffde results, 701d7d2 interpreter note).
Every verdict below was confirmed by the maintainer before this file was written.

## Rules applied (maintainer decisions, 2026-09-29)

- M4 denominator: all 30 WIDE draws whose body contains a Python traceback (20 LIB, 10 APP). Empty draws (8) and draws on
  excluded repositories (2) are not issues of the sample and are not in the denominator.
- The four checklist conditions are necessary, not sufficient: reading the issue and the fix must also show the bug is in
  scope (an exception in the repository's own code, triggerable by a reproducer).
- No identifiable fix commit (E2) => NOT_EVALUATED: the before/after oracle cannot be fixed. No exception line (E1) =>
  NOT_EVALUATED: the exception claim cannot be formulated. These draws stay in the denominator.
- A likely limitation of the tool itself does not remove a draw from M4; it shows up in M1/M2.
- Condition 1 is about what the bug needs to be reproduced, not about how the reporter demonstrated it (note 1).
- Condition 4 for every draw that met conditions 1-3 on reading was decided by the same experiment (controlled,
  wheels-only install; `INSTALL-CHECK.md`), not by reading. For the other draws it is recorded from reading only, for
  transparency; their verdict is set by E1/E2 or condition 1.
- Python 3.8 is an agreed execution fallback where the project declares no version >= 3.8; it does not mean the project
  supports 3.8.

Source key: R = from reading the issue text (and the fix diff where one exists); X = from `INSTALL-CHECK.md`.

## Checklist

| id | issue | E1/E2 | 1 network service | 2 GUI / display | 3 unsafe input | 4 installable at a stated version | verdict | reason |
|---|---|---|---|---|---|---|---|---|
| lib-01 | awslabs/gluonts#3193 | ELIGIBLE | pass R | pass R | pass R | pass X | **EVALUABLE** | bug in repository code (nursery module imports a moved module); a likely tool limitation (import-phase ModuleNotFoundError, F-004) belongs to M1/M2, not M4 |
| lib-02 | zopefoundation/RestrictedPython#181 | ELIGIBLE | pass R | pass R | pass R | pass X | **EVALUABLE** | pure Python; one call reaches the defect; fix in compile.py with a test |
| lib-03 | szaghi/MaTiSSe#41 | E2_NO_FIX_COMMIT | pass R | pass R | pass R | unknown (Python 2.7 era) | **NOT_EVALUATED** | no fix commit (E2) |
| lib-04 | oobabooga/textgen#2501 | E2_NO_FIX_COMMIT | pass R | pass R | pass R | fail R (GPU / native llama.cpp build) | **NOT_EVALUATED** | no fix commit (E2) |
| lib-05 | abhinavsingh/proxy.py#127 | ELIGIBLE | pass R (note 1) | pass R | pass R | pass X | **EVALUABLE** | defect in the HTTP parser, reachable without a running proxy; the fix test calls the parser |
| lib-06 | GlacioHack/geoutils#231 | E2_NO_FIX_COMMIT | pass R | pass R | pass R | not checked | **NOT_EVALUATED** | no fix commit (E2) |
| lib-07 | home-assistant/operating-system#2349 | E1_NO_EXCEPTION_LINE | pass R | pass R | pass R | fail R (USB accelerator hardware) | **NOT_EVALUATED** | no exception line (E1) |
| lib-08 | getsentry/sentry-python#1979 | ELIGIBLE | pass R (note 1) | pass R | pass R | pass X | **EVALUABLE** | defect in the SDK client (before_send returning None), reachable without sending events |
| lib-09 | cosmos1255/aoc_mod#10 | E2_NO_FIX_COMMIT | fail R (adventofcode.com) | pass R | pass R | not checked | **NOT_EVALUATED** | no fix commit (E2) |
| lib-10 | cornell-zhang/heterocl#260 | ELIGIBLE | pass R | pass R | pass R | fail X (native build of the in-tree TVM) | **NOT_EVALUATED** | condition 4 |
| lib-11 | giampaolo/psutil#1547 | E2_NO_FIX_COMMIT | pass R | pass R | pass R | fail R (macOS binary extension) | **NOT_EVALUATED** | no fix commit (E2) |
| lib-12 | ai2cm/ace#426 | E1_NO_EXCEPTION_LINE | pass R | pass R | pass R | not checked (large model data) | **NOT_EVALUATED** | no exception line (E1) |
| lib-13 | getsentry/sentry-python#423 | ELIGIBLE | pass R | pass R | pass R | pass X (3.8 fallback) | **EVALUABLE** | exception with traceback at interpreter exit; a likely tool limitation (printed by atexit, not raised) belongs to M1/M2, not M4 |
| lib-14 | letuananh/intsem.fx#5 | E2_NO_FIX_COMMIT | pass R | pass R | pass R | fail R (dependency lelesk not installable) | **NOT_EVALUATED** | no fix commit (E2) |
| lib-15 | tensorflow/model-optimization#753 | E2_NO_FIX_COMMIT | pass R | pass R | pass R | not checked | **NOT_EVALUATED** | no fix commit (E2) |
| lib-16 | fumitoh/modelx#43 | E2_NO_FIX_COMMIT | pass R | pass R | pass R | not checked | **NOT_EVALUATED** | no fix commit (E2) |
| lib-17 | datasciencecampus/transport-network-performance#262 | ELIGIBLE | pass R | pass R | pass R | fail X (json2html has only sdists) | **NOT_EVALUATED** | condition 4 |
| lib-18 | canonical/service-mesh#623 | E2_NO_FIX_COMMIT | fail R (Kubernetes cluster) | pass R | pass R | not checked | **NOT_EVALUATED** | no fix commit (E2) |
| lib-19 | hummingbot/hummingbot#6757 | E2_NO_FIX_COMMIT | fail R (exchange API) | pass R | pass R | not checked | **NOT_EVALUATED** | no fix commit (E2) |
| lib-20 | digitalfabrik/integreat-cms#2284 | ELIGIBLE | fail R (database server and logged-in Django session) | pass R | pass R | not checked | **NOT_EVALUATED** | condition 1 |
| app-01 | pypa/pipx#1777 | E2_NO_FIX_COMMIT | pass R | pass R | pass R | not checked (Homebrew install on macOS) | **NOT_EVALUATED** | no fix commit (E2) |
| app-02 | streamlink/streamlink#4938 | ELIGIBLE | fail R (live Twitch HLS stream) | pass R | pass R | not checked | **NOT_EVALUATED** | condition 1 |
| app-04 | httpie/http-prompt#116 | ELIGIBLE | pass R | pass R | pass R | pass X (3.8 fallback) | **EVALUABLE** | a Windows-style path is parsed as a URL scheme by urlopen; no network; not OS-specific in urlopen |
| app-05 | saulpw/visidata#851 | E2_NO_FIX_COMMIT | pass R | pass R | pass R | not checked | **NOT_EVALUATED** | no fix commit (E2) |
| app-09 | fastapi/typer#194 | E2_NO_FIX_COMMIT | pass R | pass R | pass R | not checked | **NOT_EVALUATED** | no fix commit (E2) |
| app-11 | kellyjonbrazil/jc#611 | E2_NO_FIX_COMMIT | pass R | pass R | pass R | not checked | **NOT_EVALUATED** | no fix commit (E2) |
| app-13 | kellyjonbrazil/jc#694 | E1_NO_EXCEPTION_LINE | pass R | pass R | pass R | not checked | **NOT_EVALUATED** | no exception line (E1) |
| app-16 | saulpw/visidata#2363 | E2_NO_FIX_COMMIT | pass R | pass R | pass R | not checked | **NOT_EVALUATED** | no fix commit (E2) |
| app-19 | soxoj/maigret#106 | E2_NO_FIX_COMMIT | pass R | pass R | pass R | not checked | **NOT_EVALUATED** | no fix commit (E2) |
| app-20 | nbedos/termtosvg#97 | E1_NO_EXCEPTION_LINE | pass R | pass R | pass R | not checked | **NOT_EVALUATED** | no exception line (E1) |

Note 1: lib-05 was demonstrated with a running proxy and telnet, lib-08 with a Sentry DSN; in both the defect is in code that
is reachable without that service (the parser, the client), which the fix test also shows.

## Result

**M4 = 6 / 30 = 20 %.** Below the 25 % threshold of `STOP_CRITERIA.md`: **rescope** (start
`wrong_output` support earlier). This is not a KILL; M4 never decides KILL.

Limits: 30 draws give a rough estimate (about +/- 15 percentage points); the wheels-only rule of condition 4 excludes
projects whose dependencies ship only as sdists even when they are pure Python (lib-17); the reading-based answers are
judgements recorded with their reason; 20 of the 30 draws fail on E1/E2 alone, so the share of bug reports with an
identifiable fix bounds M4 more than the checklist does.
