# Sample v3, NARROW pool: evaluability checklist (2026-09-29)

Protocol: `PROTOCOL.md` (9642a0d). Draws: `draws-narrow.json` (e0e5343), 19 of 60 eligible (E1 and E2). Condition 4 for the
candidates: `INSTALL-CHECK-NARROW.md` (71fdd27 method and predictions, b44e510 results). Rules as in `CHECKLIST-WIDE.md`.
Every verdict below was confirmed by the maintainer before this file was written.

| id | issue | verdict | reason |
|---|---|---|---|
| n-05 | davidhalter/jedi#274 | NOT_EVALUATED | the triggering input is not in the report (replayed from a saved record of a random-testing tool), so no reproducer can be written from the report |
| n-06 | python-hyper/hyperlink#51 | NOT_EVALUATED | the "fix" changes README only; the behaviour is specific to Python 2.7; not a code defect |
| n-09 | python/typeshed#1790 | NOT_EVALUATED | the repository holds type stubs, no executable code; the traceback is CPython's own behaviour |
| n-14 | PyCQA/isort#1285 | NOT_EVALUATED | packaging problem (a `tests` package shipped in the distribution); the fix changes pyproject.toml only |
| n-18 | pyasn1/pyasn1-modules#19 | NOT_EVALUATED | the failure is in the repository's test suite (a module removed from a dependency), not in the product's behaviour |
| n-23 | alexmojaki/pure_eval#11 | **EVALUABLE** | exception in the repository's code; INSTALL_OK |
| n-25 | pydantic/pydantic-settings#408 | **EVALUABLE** | exception raised through the repository's settings source; INSTALL_OK |
| n-28 | kislyuk/argcomplete#273 | NOT_EVALUATED | packaging problem (MANIFEST.in) |
| n-30 | python/typeshed#14297 | NOT_EVALUATED | type stubs, no executable code |
| n-36 | open-telemetry/opentelemetry-python-contrib#3730 | NOT_EVALUATED | condition 4: `opentelemetry-semantic-conventions==0.61b0.dev0` is an unreleased pin, no wheel (as predicted) |
| n-38 | ipython/traitlets#176 | NOT_EVALUATED | the recorded fix commit eb432cf is not reachable ("not our ref"); substituting the PR head after the run would change the oracle, so the oracle cannot be fixed |
| n-42 | googleapis/google-cloud-python#10278 | NOT_EVALUATED | CI code-generation failure; needs Docker and network (condition 1); out of scope |
| n-43 | pytest-dev/iniconfig#5 | **EVALUABLE** | fix PR #49 states "addresses #5" and opens the file with an explicit utf-8 encoding; INSTALL_OK. Needs a GBK locale at run time (see `MEASUREMENT-PROTOCOL.md`) |
| n-46 | rspeer/ordered-set#5 | **EVALUABLE** | exception in the repository's code; INSTALL_OK |
| n-49 | python-trio/trio-websocket#148 | **EVALUABLE** | condition 1 passes: the defect is in building the handshake and is reachable with a local server inside the reproducer; INSTALL_OK |
| n-50 | authlib/joserfc#50 | NOT_EVALUATED | a feature request (a missing default argument), not a bug; an observable exception before and after does not change that |
| n-56 | weaviate/weaviate-python-client#85 | NOT_EVALUATED | condition 1: constructing the client needs a running Weaviate server; the exception is raised in another CLI's code |
| n-57 | pydantic/pydantic-ai#4190 | NOT_EVALUATED | condition 4: the package reads its own installed distribution metadata at import (`PackageNotFoundError`), and the method does not install the project |
| n-59 | lincolnloop/python-qrcode#66 | **EVALUABLE** | exception through the repository's image output; INSTALL_OK. Deviation: Pillow is not declared at that commit and was added because the pre-registered table named image output |

**6 evaluable bugs** (n-23, n-25, n-43, n-46, n-49, n-59). This is below the minimum of 10 in `STOP_CRITERIA.md`: M1 and M2
from this sample are INCONCLUSIVE, fixed in advance. The sample is not extended.
