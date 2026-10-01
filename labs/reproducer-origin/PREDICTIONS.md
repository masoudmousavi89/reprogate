# Reproducer origin evidence (F-043): predictions committed BEFORE the run and BEFORE the code change

Runner: `py -3.8 labs/reproducer-origin/cases.py` (synthetic library from `tests/helpers.py`, no network, 3 runs per case).

## The gap (found by reading the code, 2026-10-01)

`--origin` accepts `ISSUE_VERBATIM_SNIPPET`, `AGENT_ADAPTED`, `AGENT_AUTHORED` or `HUMAN_AUTHORED` and writes the word into
`outcome.json`, and nothing else. The requirement (req_006, decision_007) says a verbatim snippet is a byte-identical
source span and that every adaptation records a diff and a hash. Today any origin label is accepted on trust, so a
rewritten script can be labelled `ISSUE_VERBATIM_SNIPPET`, and an adaptation leaves no trace of what it was adapted from.

## Change (the two details marked AI are the assistant's and are to be confirmed)

New optional input `origin_source` (CLI `--origin-source FILE`): the text the reproducer was taken from, for example the
code block of the issue saved as a file.
- `ISSUE_VERBATIM_SNIPPET`: `origin_source` is required and the reproducer bytes must equal it byte for byte, else
  `ValueError` before anything runs (CLI: `ERROR:` and exit code 2). The source is stored as `origin/source.txt`.
- `AGENT_ADAPTED` with a source: stored as `origin/source.txt` plus a unified diff `origin/adaptation.diff` (source to
  reproducer). Without a source: allowed, recorded as undocumented (`NONE`). (AI detail 1: an adaptation without a source is
  not an error, it is recorded as not documented.)
- `AGENT_AUTHORED` / `HUMAN_AUTHORED`: no source is expected; giving one is a `ValueError`.
- New `outcome.json` fields: `reproducer_origin_evidence` in {`IDENTICAL_TO_SOURCE`, `SOURCE_AND_DIFF`, `NONE`,
  `NOT_APPLICABLE`}, and when a source exists `reproducer_origin_source_sha256` (and `reproducer_origin_diff_sha256` for
  `SOURCE_AND_DIFF`). The files are inside the bundle, so `hashes.json` covers them.
- Invariants: when the evidence field is present it must be one of the four values and consistent with the hash fields
  (`IDENTICAL_TO_SOURCE` needs `source_sha256 == reproducer_sha256`; `SOURCE_AND_DIFF` needs both hashes); an old outcome
  without the fields stays valid (AI detail 2: no compatibility break for existing bundles).
- `replay` passes `origin/source.txt` back, so a bundle's origin is re-checked when it is replayed.

Known limit, stated before the run: byte equality shows the reproducer equals the file the maintainer supplied; it does not
prove that file is really the issue's code block (that would need a span in the raw issue body, as for claim anchors).
`AGENT_ADAPTED` with an unrelated source is accepted: the diff is evidence for a human to read, not a check.

## Predictions on the CURRENT code (baseline)
- o00 adapted, no source: runs; the outcome has no `reproducer_origin_evidence` (prints `evidence=None`).
- o01, o02, o03, o04, o07: `TypeError` (the parameter does not exist).
- o05 verbatim without a source: runs and is accepted (prints `evidence=None`): the gap.
- o06 human authored, no source: runs (`evidence=None`).
- o08, o09, o10: no bundle with the new fields, so the lines say so (`no bundle with a diff`, replay line absent or
  `ok` only if the old bundle exists, `no outcome with the new fields`). The runner prints what it can.

## Predictions for the change
- o00: ok, `evidence=NONE`, no source or diff file, no source or diff hash.
- o01: ok, `evidence=SOURCE_AND_DIFF`, source file and diff file exist, diff non-empty, both hashes recorded.
- o02: ok, `evidence=SOURCE_AND_DIFF`, diff file exists and is empty (an "adaptation" that equals its source), both hashes.
- o03: ok, `evidence=IDENTICAL_TO_SOURCE`, source file exists, no diff file, source hash recorded, no diff hash.
- o04: `ValueError (outcome.json written: False)`: one extra trailing byte is not verbatim.
- o05: `ValueError (outcome.json written: False)`.
- o06: ok, `evidence=NOT_APPLICABLE`, no source or diff.
- o07: `ValueError (outcome.json written: False)`.
- o08: the edited diff is caught: `hashes_ok=False problems=1`.
- o09: replay of the o01 bundle: `hashes_ok=True same_outcome=True`.
- o10a consistent record: `violations=0`; o10b diff hash removed: `violations=1`; o10c unknown value: `violations=1`;
  o10d old record without the fields: `violations=0`; o10e identical but source hash differs: `violations=1`.
- Unit tests: the existing 160 pass (11 skipped); new tests cover o00-o10 and one CLI exit-code check.
- Lab #1 (`run_lab001.ps1`): unchanged rows 6 of 6 (it uses the default origin, which stays valid).

## Results (recorded after the run)
(to be filled in after the run)
