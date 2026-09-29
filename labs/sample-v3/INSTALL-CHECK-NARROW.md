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

## Inventory

Written before the installs (scratch file), copied here. Affected commit = first parent of the fix; checkouts and in-repo packages on PYTHONPATH, the project itself not installed.

| id | affected commit | files read (text) | external packages and constraints (reason) | in-repo, on PYTHONPATH | interpreter (why) | top-level import |
|---|---|---|---|---|---|---|
| n-23 pure_eval | b5e1617 | setup.cfg | none (install_requires empty; pytest only in the tests extra) | repo root | 3.8 (classifiers 3.5-3.9 include 3.8) | pure_eval |
| n-25 pydantic-settings | 9b73e92 | pyproject.toml | pydantic>=2.7.0, python-dotenv>=0.21.0 (runtime) | repo root | 3.8 (requires-python >=3.8) | pydantic_settings |
| n-36 opentelemetry-instrumentation-dbapi | 0b379bef | instrumentation/opentelemetry-instrumentation-dbapi/pyproject.toml | opentelemetry-api ~= 1.12, opentelemetry-semantic-conventions == 0.61b0.dev (sibling repository opentelemetry-python, not in this repo), wrapt >= 1.0.0, < 2.0.0 (runtime) | opentelemetry-instrumentation (same repo, == 0.61b0.dev) and the dbapi package (src/) | 3.9 (requires-python >=3.9) | opentelemetry.instrumentation.dbapi |
| n-38 traitlets | not resolved | draws-narrow.json | not read: fix commit eb432cf1795bdebf92941ad1c5fa2b829486b86b is not present in the clone (`not our ref` when fetched by hash) | - | - | traitlets |
| n-43 iniconfig | 6bc5528 | setup.cfg, setup.py, pyproject.toml | none (no install_requires; setuptools_scm is a build requirement only) | src/ | 3.8 (python_requires >=3.7, classifier 3.8) | iniconfig |
| n-46 ordered-set | 10ebd50 | setup.py | none (no install_requires) | repo root (ordered_set.py) | 3.8 (classifiers 3.5-3.9 include 3.8; python_requires >=3.5) | ordered_set |
| n-49 trio-websocket | ac1c976 | setup.py | async_generator>=1.10, trio>=0.11, wsproto>=0.14 (runtime) | repo root | 3.8 (classifier 3.8; python_requires >=3.5) | trio_websocket |
| n-57 pydantic-ai | f7bf1940 | pydantic_ai_slim/pyproject.toml ([tool.hatch.metadata.hooks.uv-dynamic-versioning] dependencies, read as text), pydantic_graph/pyproject.toml | griffe>=1.14.0, httpx>=0.27, pydantic>=2.10, exceptiongroup>=1.2.2 (python < 3.11), opentelemetry-api>=1.28.0, typing-inspection>=0.4.0, genai-prices>=0.0.48 (pydantic_ai_slim); logfire-api>=3.14.1 (pydantic_graph) | pydantic_ai_slim and pydantic_graph (pydantic-graph == {{ version }} is in this repo) | 3.10 (requires-python >=3.10) | pydantic_ai |
| n-59 python-qrcode | dd30060 | setup.py | six (runtime); Pillow, unconstrained (named in the table: image output; not declared in setup.py at this commit) | repo root | 3.8 (classifiers stop at 3.4, no python_requires: agreed fallback) | qrcode |

## Results

Run 2026-09-29, Linux container, uv-managed CPython 3.8.20 / 3.9.23 / 3.10.18. Installer: `uv pip install --only-binary :all:`; a stop at the first
failure, no alternative versions. No reproducer was run and no claim was derived.

| id | interpreter | verdict | decisive line |
|---|---|---|---|
| n-23 pure_eval | 3.8 | INSTALL_OK | no dependencies to install; `import pure_eval` OK |
| n-25 pydantic-settings | 3.8 | INSTALL_OK | pydantic>=2.7.0 and python-dotenv>=0.21.0 installed from wheels; `import pydantic_settings` OK |
| n-36 opentelemetry-instrumentation-dbapi | 3.9 | NOT_EVALUATED (condition 4: `opentelemetry-semantic-conventions==0.61b0.dev0` does not exist on the index) | resolver: "there is no version of opentelemetry-semantic-conventions==0.61b0.dev0"; the package lives in the sibling repository and the pin is an unreleased development version |
| n-38 traitlets | not run | UNDETERMINED (affected commit cannot be resolved) | the fix commit `eb432cf1795bdebf92941ad1c5fa2b829486b86b` is not in the clone and `git fetch origin <hash>` returns "not our ref"; the merged PR head `refs/pull/177/head` (054c1b6) is in `main`, but it is not the recorded fix commit, so no substitute was used |
| n-43 iniconfig | 3.8 | INSTALL_OK | no dependencies to install; `import iniconfig` OK from `src/` |
| n-46 ordered-set | 3.8 | INSTALL_OK | no dependencies to install; `import ordered_set` OK |
| n-49 trio-websocket | 3.8 | INSTALL_OK | async_generator, trio, wsproto installed from wheels; `import trio_websocket` OK |
| n-57 pydantic-ai | 3.10 | UNDETERMINED (dependencies install, the top-level import needs the project's own metadata) | all 8 external dependencies installed from wheels (rc 0); `import pydantic_ai` then stops at `pydantic_ai/__init__.py:274`: `importlib.metadata.PackageNotFoundError: No package metadata was found for pydantic_ai_slim`, because the method does not install the project. All imports above that line succeeded |
| n-59 python-qrcode | 3.8 | INSTALL_OK | six and Pillow installed from wheels; `import qrcode` OK |

Method notes: Pillow for n-59 is not declared in `setup.py` at that commit; it was added because the table names image output. n-57: the dependency
list is read from the `[tool.hatch.metadata.hooks.uv-dynamic-versioning]` table as text (no project code executed); `pydantic-graph == {{ version }}` is the in-repo
`pydantic_graph`, on PYTHONPATH. n-23, n-43 and n-46 install nothing, so their INSTALL_OK says only that the checkout imports with the interpreter alone.
No operator correction was needed in this run.

## Misses

Prediction: n-23, n-25, n-38, n-43, n-46, n-49, n-57, n-59 INSTALL_OK; n-36 NOT_EVALUATED (condition 4).
- n-36: matched (NOT_EVALUATED, condition 4, the development pin has no release).
- n-38: predicted INSTALL_OK, result UNDETERMINED (fix commit not fetchable). **Miss.**
- n-57: predicted INSTALL_OK, result UNDETERMINED (import needs the installed distribution's metadata). **Miss.**
- n-23, n-25, n-43, n-46, n-49, n-59: matched.
