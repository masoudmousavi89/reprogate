# Adversarial corpus index (req_012): the one class without a committed end-to-end run, predictions BEFORE the run

`CORPUS.md` maps every class listed in req_012 to committed files and recorded results. While building it, one class had only a
gate unit test (`tests/test_gate.py::test_mocking_and_patching_rejected`) and finding F-013 (scratch reproducers that were not
committed): mock / monkeypatch of the target. A committed fixture is added so the class has a reproducible end-to-end run:
`labs/jinja-843/fixtures/f05_patch_target.py` replaces `LRUCache.__setitem__` of the target library with a function that raises
`IndexError`-like behaviour (`deque().popleft()`), then calls it.

Run on the Lab #1 pre-fix commit 81825095 (the real checkout, exact blobs via `--checkout-sha`), pinned MarkupSafe 2.0.1 venv, frozen claim of Lab #1,
host mode (Windows, py -3.8). Runner: `labs/adversarial-corpus/run_f05.py`.

| item | predicted |
|---|---|
| real tool, real gate | gate REJECTED with code `PATCHES_TARGET` (an assignment to an attribute of the imported name `utils`) -> `NOT_EVALUATED / REPRODUCER_REJECTED`, no run executed |
| same reproducer with the gate bypassed (`gate=False`, as the earlier attack labs do; the real gate is not changed) | the exception comes from the reproducer's own function, so the matcher finds no TARGET frame (the observer sees the frame in the reproducer file): `NO_MATCHING_REPRODUCTION_FOUND / NONE`, never SYMPTOM_REPRODUCED |
| source repository | unchanged (the checkout is an export; source `.git` hash identical) |

Not covered: other patching forms the gate may miss (for example through `sys.modules` or `vars()`), Linux/Docker for this fixture.
