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
