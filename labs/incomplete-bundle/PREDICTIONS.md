# Incomplete and unreadable bundles (F-035): predictions committed BEFORE the code change and BEFORE the run

Runner: `py -3.8 labs/incomplete-bundle/cases.py` (synthetic bundles in a temporary folder, CLI called in-process; no
reproducer is executed because every verify case stops before replay).

Problem (open point of F-029): `inspect` on a bundle without `outcome.json` stops with a `FileNotFoundError` traceback
and exit 1, the same code as a bundle that is readable but invalid. A script cannot tell "the bundle is invalid" from
"the tool crashed".

Founder decision (2026-09-29, exit-code mapping): exit 1 = the bundle is readable but invalid, or verify failed; exit 2 =
incomplete input. Defined precisely here:

- `INVALID_BUNDLE`, exit 2, message on stderr naming every problem: the evidence path is not a folder, or a JSON file the
  command must read is missing, unreadable or not valid JSON. `inspect` needs `outcome.json`; `verify` needs
  `outcome.json`, `environment.json` and `claim.json`. The check runs before anything else (before the host-execution
  flag in `verify`; it executes nothing).
- Everything that is readable is judged as before: hash problems and invariant violations keep exit 1 in `verify`, and
  `inspect` keeps exit 1 for invariant violations. A readable `outcome.json` that is not an object is an invariant
  violation (`MISSING_FIELD`, the validator already says so), not `INVALID_BUNDLE`.
- `inspect` no longer indexes fields the validator does not require (`reproducer_name`, `sandbox`, ...); a missing one
  prints `-`. The validator contract (F-029) is unchanged.
- `INVALID_BUNDLE` is a CLI error, not an outcome: no enum, schema or `outcome.json` changes.

## Baseline (code after F-034): predicted

| case | command | predicted |
|---|---|---|
| b01 path absent | inspect | CRASH FileNotFoundError |
| b02 empty folder | inspect | CRASH FileNotFoundError |
| b03 real shape (claim, gate, reproducer only) | inspect | CRASH FileNotFoundError |
| b04 outcome.json deleted after hashing | inspect | CRASH FileNotFoundError |
| b05 outcome.json not valid JSON | inspect | CRASH JSONDecodeError |
| b06 outcome.json is a JSON list | inspect | CRASH TypeError |
| b07 valid outcome without `sandbox` | inspect | CRASH KeyError |
| b08 complete valid bundle | inspect | exit 0 |
| b09 impossible outcome, hashes regenerated | inspect | exit 1 |
| b10 real shape | verify | exit 1 (hashes.json missing) |
| b11 outcome.json deleted after hashing | verify | exit 1 (missing file) |
| b12 claim.json deleted, hashes regenerated | verify | CRASH FileNotFoundError |
| b13 environment.json not valid JSON, hashes regenerated | verify | CRASH JSONDecodeError |
| b14 impossible outcome, hashes regenerated | verify | exit 1 |
| b15 real shape, no `--allow-host-execution` | verify | exit 2 (host warning), no INVALID_BUNDLE |

## Predictions for the change

| case | predicted |
|---|---|
| b01 | exit 2, INVALID_BUNDLE (not a folder) |
| b02, b03, b04 | exit 2, INVALID_BUNDLE (missing outcome.json) |
| b05 | exit 2, INVALID_BUNDLE (outcome.json is not valid JSON) |
| b06 | exit 1, MISSING_FIELD, no crash |
| b07 | exit 0, `sandbox` printed as `-` (the validator does not require it) |
| b08 | exit 0, unchanged |
| b09 | exit 1, unchanged |
| b10 | exit 2, INVALID_BUNDLE (missing environment.json and outcome.json); was exit 1 |
| b11 | exit 2, INVALID_BUNDLE (missing outcome.json); was exit 1 |
| b12 | exit 2, INVALID_BUNDLE (missing claim.json) |
| b13 | exit 2, INVALID_BUNDLE (environment.json is not valid JSON) |
| b14 | exit 1, unchanged |
| b15 | exit 2, INVALID_BUNDLE reported before the host warning |

- Unit tests: the existing 127 pass; new tests cover the cases above plus `verify` through the CLI on a real, complete
  bundle of the synthetic library (exit 0, unchanged).
- Real local bundles (ignored folders `labs/jinja-843/evidence-20260929-032443` and `-032643`, 14 bundles): the 13 with an
  `outcome.json` keep `inspect` exit 0 with `invariants: OK` and identical printed lines; the interrupted
  `f04_subclass_override` of the first folder changes from a traceback to exit 2 with `INVALID_BUNDLE: missing outcome.json`.

Not covered by this change (recorded, not fixed): `inspect` still ignores hash problems in its exit code; `verify` can
still crash on readable JSON with missing keys (for example `environment.json` without `git`, or `outcome.json` without
`reproducer_name`) and on a missing reproducer file when `hashes.json` was regenerated. Linux and Docker are not run.
