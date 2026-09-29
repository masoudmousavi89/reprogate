# Preliminary M1/M2 measurement on the NARROW sample (protocol, fixed before any reproducer is written)

Status fixed in advance: 6 evaluable bugs (`CHECKLIST-NARROW.md`) is below the minimum of 10 in `STOP_CRITERIA.md`. The
result is **PRELIMINARY / INCONCLUSIVE (<10)** whatever the numbers are. No accuracy, coverage or generalisation claim is made
from it; it only informs the choice between a second round (`STOP_CRITERIA.md`) and the rescope to `wrong_output`.
Maintainer decisions of 2026-09-29.

Bugs: n-23 pure_eval#11, n-25 pydantic-settings#408, n-43 iniconfig#5, n-46 ordered-set#5, n-49 trio-websocket#148,
n-59 python-qrcode#66. Affected commits and dependency sets: `INSTALL-CHECK-NARROW.md`.

## 1. Reproducers from a blind session

- Environment: a separate repository and cloud session that has no access to this repository, its findings, fixtures or
  labs. Fallback if that is not workable: a separate desktop session in an empty folder, blind by instruction only; the
  fallback and its weaker isolation are recorded if used.
- Input: `blind-input/ISSUES.md` (title and body of each report, verbatim, no comments; sha256
  fa55e4eaec5a5ad6eb053ec3b66b185d798f9bd475f8e99f27271371eb8d007c) and `blind-input/PROMPT.md` (the task text; sha256
  4a2c3f5b7dc6a36fb9135887eaa5e402772866d24d8c4ea7d0a23b06e308b681). The session gets only the affected commit (depth-1
  fetch), so the fix is not in its history.
- The session may run its scripts against the affected commit.
- Three attempts per bug, each in its own new session (ATTEMPT = 1, 2, 3), so the attempts do not see each other:
  18 reproducers. Each attempt saves `repro.py`, `run.txt` (stdout, stderr, exit code of one final run) and `notes.md`.
- Known limit: the blind sessions may belong to the same model family that helped design this tool.

## 2. Human labels (before the fix and before ReproGate)

Order: issue + affected checkout -> reproducer -> human label -> freeze/commit -> fix diff -> ReproGate.

- The maintainer labels each of the 18 reproducers CORRECT (triggers the reported bug for the reported reason) or
  INCORRECT (anything else, including "could not trigger it"). The label sheet shows only the report text, `repro.py`,
  `run.txt` and `notes.md`. It does not show the fix diff or any ReproGate output. The AI assembles the sheet and does not
  label. Labels are a preliminary annotation (one human).
- Labels are committed before the fix diffs are shown and before any ReproGate run. A label that later looks wrong is
  reported, never edited.

## 3. Mutations (supplement, capped)

- Catalog, fixed now: MUT-1 replace the trigger with a direct `raise` of the claimed type and message; MUT-2 remove the
  statement(s) that call into the project after the setup; MUT-3 raise the claimed type and message from a function defined
  in the reproducer; MUT-4 wrap the trigger in `try/except Exception` and raise the claimed type with the report's message;
  MUT-5 replace the trigger with printing the report's traceback text to stderr and `sys.exit(1)`.
- Cap (`STOP_CRITERIA.md`: mutations are at most half of the bad set): the number of mutations is at most the number of
  blind reproducers labelled INCORRECT.
- Selection, mechanical: CORRECT-labelled blind reproducers in the fixed order n-23, n-25, n-43, n-46, n-49, n-59 and attempt
  1, 2, 3; mutation types in turn MUT-1 .. MUT-5; stop at the cap. Mutations are INCORRECT by construction. They are
  generated and committed after the labels and before any ReproGate run.

## 4. Claims

Mechanical, from the report text only: `exception_type` and `message` from the last exception line of the report's
traceback; `location` from the innermost frame of that traceback whose file lies inside the project package; anchors are
those exact strings as they appear in the report. `claim-check` on the raw report body (desktop, GitHub API) gives
`claim.frozen.json`; if provenance is insufficient the run uses `--allow-unverified-provenance` and the qualifier is kept.
Claims are committed before any run and are never edited to change an outcome.

## 5. Run

- Linux, `--sandbox docker`, one image per bug built from `python:3.8-slim` with the wheels-only dependency set of
  `INSTALL-CHECK-NARROW.md` (Pillow for n-59 as recorded). The image recipes are committed before the run.
- n-43 needs a GBK locale: its image generates `zh_CN.GBK` and sets the locale. If the environment cannot provide it, the
  reproducer is not removed; the failure counts in M2 as not accepted.
- For every blind reproducer and mutation: `reprogate oracle` with the affected commit as before, the fix commit as after,
  `--runs 5`.
- Expected outcomes are derived mechanically from the labels and committed before the run: CORRECT -> oracle PASS;
  INCORRECT -> not `SYMPTOM_REPRODUCED` / `SYMPTOM_REPRODUCED_FLAKY` on the affected commit.

## 6. Metrics (as in `STOP_CRITERIA.md`)

- Bad set = blind reproducers labelled INCORRECT + mutations. M1 = members whose outcome on the affected commit is
  `SYMPTOM_REPRODUCED` or `SYMPTOM_REPRODUCED_FLAKY`, divided by the bad set.
- Good set = blind reproducers labelled CORRECT. M2 = members with oracle PASS, divided by the good set; an environment
  failure counts as not accepted.
- Reported with numerators, denominators and per-bug rows, labelled PRELIMINARY / INCONCLUSIVE (<10).
