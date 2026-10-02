# Wheelhouse environment: results (Windows, py -3.8.10, 2026-10-02; runner `run_wheelhouse.ps1`, log `run-windows-2026-10-02.log`)

Predictions: `PREDICTIONS.md`, committed first as 156f668. All predicted rows held; no prediction miss.

| item | predicted | observed |
|---|---|---|
| download of the 8 versions | all 8 cp38 win_amd64 wheels | 8 of 8, exit 0; `wheelhouse.sha256.txt` lists the SHA-256 of each; files set read-only (8 of 8) |
| unconstrained `MarkupSafe>=0.23` | 2.1.5 | MarkupSafe-2.1.5-cp38-cp38-win_amd64 |
| `--no-index` install | works for all | exit 0 for all 8 (plus the two rebuilds) |
| `import jinja2` from the pre-fix checkout | 2.0.x ok, 2.1.x fail, boundary 2.1.0 (hypothesis) | 2.0.0 and 2.0.1 import; 2.1.0 .. 2.1.5 all fail with `ImportError: cannot import name 'soft_unicode' from 'markupsafe'`. The boundary is 2.1.0; the range 2.0.1 to 2.1.5 is now tested |
| rebuild determinism | identical installed markupsafe files | identical (True) |
| oracle with the wheelhouse-built 2.0.1 template | ORACLE PASS, FRESH_COPY_PER_RUN, hash recorded and unchanged | before SYMPTOM_REPRODUCED, after NO_MATCHING_REPRODUCTION_FOUND, post-fix CLEAN_COMPLETION, ORACLE PASS; mode FRESH_COPY_PER_RUN, 584 files, template tree hash 1ec8da5c... identical before and after |
| run with the 2.1.5 template | ENV_FAILURE | NOT_EVALUATED / ENVIRONMENT_UNAVAILABLE, 5 of 5 runs ENV_FAILURE |

## Limits (what this does not show)
- Windows, cp38-win_amd64 wheels only. A Linux wheelhouse was not built.
- `--no-index` stops pip from using an index; the machine was online. A network-less build machine is not proven.
- The runtime set of this lab is one package (MarkupSafe). A set with several packages, a transitive dependency or an
  sdist-only release was not tested. A pre-built historical venv would still be needed for those (decision_072).
- `environment_trust` stays UNVERIFIED in `environment.json`: the tool records the template hash but not the hashes of the
  wheels it came from; the link between `wheelhouse.sha256.txt` and the template is only in this lab's log.
- The version to install (2.0.1) was chosen by me from the boundary search; the tool does not choose it.
