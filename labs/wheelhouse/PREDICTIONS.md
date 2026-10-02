# Wheelhouse environment (req_004, oq_003, decision_072): predictions committed BEFORE the run

Question (oq_003): can the whole historical dependency set of Lab #1 be downloaded with
`pip download --python-version 3.8 --only-binary=:all:` into a wheelhouse that is then frozen read-only, and can the
target environment be built from it with `--no-index` so that the Lab #1 oracle still passes?

Scope facts read from the repository before the run (not from memory): `jinja-before` (81825095) declares
`install_requires=["MarkupSafe>=0.23"]` and `extras_require={"i18n": ["Babel>=0.8"]}`. The reproducer imports only jinja2 and
MarkupSafe, so the "whole historical dependency set" of the runtime is MarkupSafe alone (Babel is an optional extra, not part
of the runtime set and not downloaded). Host: Windows, `py -3.8` (3.8.10), so the wheels are `cp38-win_amd64`. A Linux
wheelhouse is NOT covered by this run. "No network" is enforced only by `--no-index` (pip never contacts an index); the
machine itself stays online, so a network-less sandbox is not proven here.

Steps (runner: `run_wheelhouse.ps1`): (1) download MarkupSafe 2.0.0, 2.0.1, 2.1.0 .. 2.1.5 one by one into one wheelhouse, record
SHA-256 of every wheel, mark the files read-only; also record what an unconstrained `MarkupSafe>=0.23` download resolves to
(separate folder, not in the wheelhouse); (2) for every version build a fresh venv with `pip install --no-index --find-links
<wheelhouse> MarkupSafe==V` and try `import jinja2` from the pre-fix checkout; (3) build the template venv twice from the
wheelhouse (2.0.1) and compare the installed markupsafe files; record the template tree hash; (4) run the jinja oracle
(`--env-template` = the wheelhouse-built 2.0.1 venv) and one `run` on the 2.1.5 venv.

## Predictions
| item | predicted |
|---|---|
| download of the 8 versions | all 8 wheels are available for cp38 win_amd64 and download; wheelhouse complete |
| unconstrained `MarkupSafe>=0.23` | resolves to 2.1.5 (newest with a cp38 wheel) |
| `import jinja2` per version | 2.0.0 and 2.0.1 succeed; 2.1.x fail with ImportError. My guess is that the boundary is 2.1.0 (MarkupSafe 2.1.0 removed `soft_unicode`); this is a hypothesis, not a known fact, and the run decides |
| `--no-index` install | works for every version with no index access (pip never downloads) |
| rebuild determinism | identical installed markupsafe file hashes in both builds; whole-venv tree hashes may differ (pyvenv.cfg, paths, bytecode), so the tree hash recorded by the tool is for the template that is actually used |
| oracle with the wheelhouse-built 2.0.1 template | ORACLE PASS (before SYMPTOM_REPRODUCED, after clean completion), `environment_isolation.mode` FRESH_COPY_PER_RUN, template tree hash recorded and unchanged after the run |
| run with the 2.1.5 template | ENV_FAILURE for all runs (not a mismatch) |

Done for req_004 if: the wheelhouse is complete and frozen with hashes, the oracle passes with an environment built from it by
`--no-index`, and the tree hash is recorded. Any other result is also recorded as a finding (decision_072): if the
wheelhouse cannot be built, a finding for a controlled online dependency mode is opened.

Not covered: Linux wheelhouse, dependencies with sdist-only releases, transitive dependencies (none here), proof of a
network-less machine, other labs.
