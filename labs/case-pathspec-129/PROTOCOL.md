# Case study: `wrong_output` on one real bug (python-pathspec #129): protocol and predictions fixed before the run

Status: pre-registered 2026-10-01, before the claim is frozen against the raw issue body and before any run. This is a
single case study, not a pilot: it says nothing about coverage, accuracy or reliability. `wrong_output` stays EXPERIMENTAL.

## Why this case, said openly

The two pilots (`labs/wrong-output-pilot/`, `labs/wrong-output-pilot-2/`) found no evaluable candidate, so the tool has never
run on a real `wrong_output` bug. This bug was seen in a screening run of pilot 2 that did not apply that pilot's exclusion
rule correctly, and it was removed from pilot 2 for that reason. It is chosen here knowing that it fits, so the choice is
**not blind** and the case does not count as an unseen sample. The goal is one honest end-to-end run of the mechanism on a
real bug, with the answer key written by the project's own maintainers.

## What was read before this protocol (nothing about the fix was used for the claim)

- Issue #129: the call `GitIgnoreSpec.from_lines(["build", "!keep.log"]).match_file("build/keep.log")` returns `False`
  (shown as `# -> False`) and "should be ignored", i.e. `True`.
- Pull request #132, merged 2026-09-05, merge commit `f404ca47871a9f2f854bbadc5cb3d77155f64db3`, first parent (the
  affected commit) `93e0179cb2d7a6d830050c62f3eab950b9263bf3`. Its regression tests are `GitIgnoreSpecTest.test_10_issue_129_a`,
  `_b` and `_c` in `tests/test_06_gitignore.py`. The assistant has seen the changed-file list and the test patch of that pull
  request while screening; the claim below does not use them.
- `pyproject.toml` at the affected commit: `requires-python >=3.9`, no runtime dependencies (optional extras only).
- The only code lookup made for the claim: `GitIgnoreSpec` (in `pathspec/gitignore.py`) does not define `match_file`; it
  inherits `PathSpec.match_file` from `pathspec/pathspec.py`, which returns `bool(include)`. So the claim's target is
  `pathspec/pathspec.py` `match_file`. This lookup of the file for the named function is the one difference from the pilot
  rule "claim from the issue text only".

## Environment

Linux, CPython 3.9 (the lowest declared version >= 3.8; Python 3.9 is not installed on the Windows machine), a fresh
virtual environment, no network during the run, the project checkout on `PYTHONPATH`, the project not installed. Optional
extras (hyperscan, re2) are not installed, so the default backend is the pure-Python one. Run by the cloud session; the
desktop session reviews the commit.

## Method, in this order

1. The claim (`labs/case-pathspec-129/claim.json`, committed with this protocol) is frozen as written; it is not edited.
   `claim-check` is run against the raw issue body (`tools/fetch_issue.py --repo cpburnz/python-pathspec --number 129`).
2. The reproducer is the code block of the issue, byte for byte, saved as the origin source and run with
   `--origin ISSUE_VERBATIM_SNIPPET --origin-source <file>` (the first real use of F-043). The block ends in a comment
   and prints nothing, so it needs no adaptation; if the block is not byte-identical to what the gate accepts, that is a result.
3. Answer key: the three regression tests are run on the affected commit and on the merge commit. Expected: they fail before
   and pass after. If not, no verdict is recorded and the case is `ENV_FAILED` or `TOOL_DISAGREES` with the reason.
4. The tool: `oracle`, 5 runs per commit, twice: **(a)** with the claim frozen by `claim-check`, **(b)** with the unfrozen
   claim and `--allow-unverified-provenance` (recorded as `PROVENANCE_UNVERIFIED`).
5. The outcome is compared with the answer key. Neither side is changed after seeing the other.

## Predictions (fixed before the run)

- (a) Frozen with `claim-check`: `provenance_sufficient` is False, because the sufficiency rule exists for exception claims
  only (it needs an `exception_type` anchor). The outcome on the affected commit is `INCONCLUSIVE` with reason
  `CLAIM_PROVENANCE_INSUFFICIENT`, the oracle does not pass. If this is right it is a finding: provenance sufficiency is not
  defined for `wrong_output` claims.
- (b) Unverified provenance: on the affected commit `SYMPTOM_REPRODUCED` with 5 of 5 runs, the recorded return of
  `PathSpec.match_file` being `False` from an authentic TARGET frame; on the merge commit a clean completion with the return
  `True`; the oracle passes; the qualifier is `PROVENANCE_UNVERIFIED`; `oracle_required` is true for the single run outcome.
- The reproducer origin is recorded as `IDENTICAL_TO_SOURCE`.
- The answer key: the three tests fail on the affected commit and pass on the merge commit.
- The static gate accepts the reproducer (VALID).
- I do not know whether the optional-backend sub-tests are skipped without hyperscan and re2; that is recorded, not predicted.

## Result labels (one, no others)

`TOOL_AGREES` (oracle PASS and the answer key fails before and passes after, in the unfrozen run (b)), `TOOL_DISAGREES`
(any other combination where the claim and environment were fine; a finding), `CLAIM_NOT_EXTRACTABLE`,
`ENV_FAILED`. Run (a) is reported separately as a finding about provenance, whatever it shows.

## Limits (stated before the run)

- One bug, chosen knowing it fits: it shows whether the mechanism runs end to end on a real bug, not how often it would.
- The answer key is the maintainers' own test, written with knowledge of the fix; agreement does not make the tool
  independent of the project.
- The reproducer is the issue's own block, so it does not test whether the tool can tell good from bad reproducers.
- A reproducer that imitates the observation protocol (w09, b05) is still accepted; this case does not test that.
- The run happens on Linux only. No threshold, no percentage, and no accuracy claim comes out of this case.

## Results (recorded after the run)
(to be filled in after the run)
