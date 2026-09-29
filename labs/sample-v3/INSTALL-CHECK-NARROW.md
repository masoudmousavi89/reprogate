# Sample v3, NARROW: controlled dependency-install check (condition 4), method and predictions committed before the run

Scope: the 9 NARROW candidates kept after reading (n-23, n-25, n-36, n-38, n-43, n-46, n-49, n-57, n-59). The other 10
eligible NARROW draws are NOT_EVALUATED on reading (maintainer decision, 2026-09-29). No reproducer is run in this step.

Status fixed in advance: 9 is below the minimum of 10 bugs in `STOP_CRITERIA.md`, so M1/M2 from this sample are
INCONCLUSIVE whatever happens. Any later M1/M2 figure from these bugs is PRELIMINARY and supports no accuracy or coverage
claim.

Method: identical to `INSTALL-CHECK.md` (7f1ffa6), including the Python 3.8 fallback note (701d7d2), with one addition for
monorepos: packages that live in the same repository as the affected component are project code and go on PYTHONPATH;
only dependencies from outside the repository are installed.

| id | repository | fix commit | component named in the issue |
|---|---|---|---|
| n-23 | alexmojaki/pure_eval | 84c34b6d63a5 | pure_eval |
| n-25 | pydantic/pydantic-settings | fdd666bf9436 | pydantic_settings |
| n-36 | open-telemetry/opentelemetry-python-contrib | 3b357c07a899 | opentelemetry-instrumentation-dbapi |
| n-38 | ipython/traitlets | eb432cf1795b | traitlets |
| n-43 | pytest-dev/iniconfig | 5f617e30ac0c | iniconfig |
| n-46 | rspeer/ordered-set | 7503d88c67b1 | ordered_set |
| n-49 | python-trio/trio-websocket | 61258058db3f | trio_websocket |
| n-57 | pydantic/pydantic-ai | dab3d727d5c5 | pydantic_ai (pydantic_ai_slim) |
| n-59 | lincolnloop/python-qrcode | 0a9f17d3afb0 | qrcode (image output needs Pillow) |

Predictions: n-23, n-25, n-38, n-43, n-46, n-49, n-57, n-59: INSTALL_OK. n-36: NOT_EVALUATED, condition 4 (the component
pins dependencies from the sibling opentelemetry-python repository to unreleased development versions, so no wheel exists).
