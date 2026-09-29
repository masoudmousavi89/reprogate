# Sample v3: controlled dependency-install check (condition 4), method and predictions committed before the run

Scope: the WIDE candidates that meet conditions 1-3 on reading (lib-01, lib-02, lib-05, lib-08, lib-10, lib-13, lib-17, app-04).
Condition 4 is decided for all of them by the same experiment, not by reading. No reproducer is run in this step.

Method (maintainer decision, 2026-09-29):
- Affected commit = first parent of the fix commit recorded in draws-*.json.
- Declared dependencies are read as text from the affected commit (pyproject.toml, setup.cfg, requirements*.txt,
  setup.py read without executing it): runtime dependencies plus any extra that the code path named in the issue needs,
  each with the reason. If they cannot be determined without executing project code, the candidate is UNDETERMINED
  (a maintainer decision, not an automatic verdict).
- Interpreter: Python 3.8 if the affected commit declares support for it, otherwise the lowest declared version >= 3.8;
  recorded.
- The inventory (packages and version constraints) is written below before the install.
- Install: a fresh venv, `pip install --only-binary=:all:` with exactly the declared constraints. The practical criterion
  is to avoid source builds (sdists) and running build or setup code. The project itself is not installed: its checkout
  goes on PYTHONPATH.
- A dependency without a usable wheel, or a project whose own code needs a native build before it can run: stop that
  candidate, NOT_EVALUATED, condition 4, with the package named. No credentials; nothing is run besides pip and an
  `import` of the top-level package to confirm the install.

Predictions: lib-01, lib-02, lib-05, lib-08, lib-13, lib-17, app-04: INSTALL_OK. lib-10 (heterocl): NOT_EVALUATED,
condition 4 (its in-tree TVM needs a native build).

## Inventory

Written before the installs (scratch file), copied here. Affected commit = first parent of the fix; checkouts on PYTHONPATH, project not installed.

| id | affected commit | files read (text) | packages and constraints (reason) | interpreter (why) | top-level import |
|---|---|---|---|---|---|
| lib-01 gluonts | b97ff43 | setup.cfg, requirements/requirements.txt, requirements/requirements-pytorch.txt | numpy~=1.16, pandas>=1.0,<3, pydantic>=1.7,<3, tqdm~=4.23, toolz~=0.10, typing-extensions~=4.0 (runtime); torch>=1.9,<3, lightning>=2.2.2,<2.4, pytorch_lightning>=2.2.2,<2.4, scipy~=1.10 (pytorch extra: the issue is in the torch code of gluonts.torch) | 3.8 (python_requires >= 3.7) | gluonts |
| lib-02 RestrictedPython | f1f1bdb | setup.py, tox.ini | none (install_requires empty) | 3.8 (classifier 3.8, python_requires >=2.7,<3.10) | RestrictedPython (src/) |
| lib-05 proxy.py | 69445a8 | setup.py, requirements.txt | typing-extensions==3.7.4 (runtime) | 3.8 (classifier 3.8) | proxy |
| lib-08 sentry-python | 16f14ec | setup.py | urllib3>=1.26.11 (python_version >= 3.6), certifi (runtime); no extra: before_send is core client code | 3.8 (classifier 3.8) | sentry_sdk |
| lib-10 heterocl | 07b7fd7 | python/setup.py | numpy==1.18.5, decorator, networkx, matplotlib, backports.functools_lru_cache, ordered_set, xmltodict, tabulate, sodac (runtime); in-tree TVM (tvm/, python/heterocl) is not a package | 3.8 (no python_requires, no version classifier; 3.8 is the floor) | heterocl (python/) |
| lib-13 sentry-python | a50b651f | setup.py | urllib3, certifi (runtime); no extra (transport/worker code) | 3.8 (classifiers stop at 3.7, no python_requires cap; 3.8 is the floor) | sentry_sdk |
| lib-17 transport-network-performance | 51ee214 | pyproject.toml, requirements.txt | pyproject declares no dependencies; requirements.txt is the only declaration and is installed whole (r5py==0.1.0, gtfs_kit==5.2.7, pyproj>=3.6.0, pandas<2.1.0, ... and the unpinned rest) | 3.9 (requires-python >=3.9,<3.10) | transport_performance (src/) |
| app-04 http-prompt | 56448cd | setup.py, requirements.txt | click>=5.0, httpie>=0.9.2, parsimonious>=0.6.2, prompt-toolkit>=0.60, Pygments>=2.1.0, six>=1.10.0 (runtime) | 3.8 (classifiers stop at 3.6, no python_requires; 3.8 is the floor) | http_prompt |

## Results

Run 2026-09-29, Linux container, uv-managed CPython 3.8.20 / 3.9.23. Installer: `uv pip install --only-binary :all:` (same wheels-only rule as
`pip install --only-binary=:all:`, but not literally `pip`); a stop at the first failure, no alternative versions tried.

| id | interpreter | verdict | decisive line |
|---|---|---|---|
| lib-01 gluonts | 3.8 | INSTALL_OK | install rc 0 (torch, lightning, pytorch_lightning wheels resolved); `import gluonts` OK |
| lib-02 RestrictedPython | 3.8 | INSTALL_OK | nothing to install (no declared dependencies); `import RestrictedPython` OK from `src/` |
| lib-05 proxy.py | 3.8 | INSTALL_OK | `typing-extensions==3.7.4` installed; `import proxy` OK |
| lib-08 sentry-python | 3.8 | INSTALL_OK | `urllib3>=1.26.11`, `certifi` installed; `import sentry_sdk` OK |
| lib-10 heterocl | 3.8 | NOT_EVALUATED (condition 4: native build) | all declared dependencies installed (incl. `numpy==1.18.5`, `sodac`), but `import heterocl` raises `RuntimeError: Cannot find the files.` listing the missing `libhcl_runtime.so` (in-tree TVM is not built) |
| lib-13 sentry-python | 3.8 | INSTALL_OK | `urllib3`, `certifi` installed; `import sentry_sdk` OK |
| lib-17 transport-network-performance | 3.9 | NOT_EVALUATED (condition 4: `json2html` has no wheel) | `uv` resolution of `requirements.txt` fails: `json2html` (required by `gtfs-kit==5.2.7`) has only sdists, "Wheels are required for `json2html` because building from source is disabled" |
| app-04 http-prompt | 3.8 | INSTALL_OK | click, httpie, parsimonious, prompt-toolkit, Pygments, six installed; `import http_prompt` OK |

Method notes: for lib-17 the line `-e .` of `requirements.txt` (install of the project itself) was removed, following the method (project not
installed); the first two attempts failed only because of that line, not because of a package. `python_requires` is absent or capped at 3.7
classifiers for lib-10, lib-13 and app-04, so 3.8 was used as the floor (the method's "lowest declared >= 3.8" has no declared value there).
lib-01 and lib-17 have no import beyond the top-level package here; no reproducer was run and no claim was derived.

## Misses

Prediction: seven INSTALL_OK and lib-10 NOT_EVALUATED (condition 4).
- lib-17: predicted INSTALL_OK, result NOT_EVALUATED (condition 4, `json2html` sdist only). **Miss.**
- The other seven matched: lib-01, lib-02, lib-05, lib-08, lib-13, app-04 INSTALL_OK; lib-10 NOT_EVALUATED (dependencies install, but the project's own native library is not built).

## Maintainer note on the interpreter (2026-09-29)

For lib-10, lib-13 and app-04 the project metadata declares no Python version >= 3.8 (no `python_requires` and classifiers
that stop below 3.8, or none). Python 3.8 was used there as an agreed execution fallback, not because the project states
support for it. For these three, INSTALL_OK (and lib-10's result) means "the declared dependencies install as wheels on
Python 3.8 in this environment", not "the project supports Python 3.8".

lib-17 stays NOT_EVALUATED: `json2html` being sdist-only is a measured outcome of condition 4 under the fixed method; the
method is not changed. Its prediction miss is recorded separately above and does not alter that outcome.
