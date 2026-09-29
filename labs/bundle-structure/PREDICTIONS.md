# Hash problems in inspect, structure check in verify (F-036): predictions committed BEFORE the code change and BEFORE the run

Runner: `py -3.8 labs/bundle-structure/cases.py` (synthetic bundles built with the helpers of `labs/incomplete-bundle/cases.py`,
CLI called in-process; no reproducer is executed: every verify case stops before one could run).

Problems left open by F-035:
1. `inspect` ignores hash problems in its exit code: an outcome edited WITHOUT regenerating `hashes.json` gives exit 0,
   while the same edit WITH regenerated hashes gives exit 1 (invariants). A bundle without `hashes.json` also gives 0.
2. `verify` crashes with a traceback on readable JSON that lacks a key it uses, or on a missing reproducer file, when
   `hashes.json` was regenerated. The exit code is already non-zero (fail-closed), but the cause is not named.
3. Seen while reading the code for this finding: `outcome.json` field `reproducer_name` is joined to `reproducer/` without
   a check, so a bundle with regenerated hashes can point `verify` at a file OUTSIDE the bundle, which no hash covers (the
   static gate still runs on it).

Founder decisions (2026-09-29): (A) a hash problem makes `inspect` exit 1, and `hashes.json` becomes a required file for
both commands (missing or not valid JSON => `INVALID_BUNDLE`, exit 2); (B) `verify` gets an explicit structure check,
not a catch-all, with exit 1 and each problem named.

Defined precisely:
- Required files: `inspect` = `outcome.json`, `hashes.json`; `verify` = `outcome.json`, `environment.json`, `claim.json`,
  `hashes.json`. A readable `hashes.json` without a `files` object is a hash problem (exit 1), not a crash.
- Structure check in `replay`, after hashes and invariants and before anything runs (no `git`, no interpreter, no replay):
  `environment.json` has `git.commit` (the value may be null); `claim.json` is an object with a `claim` object;
  `outcome.json` has `reproducer_name` as a plain file name (no folder part, not `.`/`..`), `reproducer_origin` as a
  string, `runs_requested` as an integer >= 1 and `attempts_before_submission` as an integer >= 0; the file
  `reproducer/<reproducer_name>` exists. Problems are reported as `structure_problems` and printed as `STRUCTURE:` lines;
  verify prints `VERIFY FAIL` and exits 1.

## Baseline (code after F-035): predicted

| case | command | predicted |
|---|---|---|
| h01 gate.json edited after hashing | inspect | exit 0 |
| h02 file added after hashing | inspect | exit 0 |
| h03 recorded file removed | inspect | exit 0 |
| h04 hashes.json missing | inspect | exit 0 |
| h05 hashes.json missing | verify | exit 1 |
| h06 hashes.json not valid JSON | inspect | CRASH JSONDecodeError |
| h07 hashes.json not valid JSON | verify | exit 2 (generic `ERROR:` through the ValueError handler, as learned in F-035 b13), no INVALID_BUNDLE |
| h08 hashes.json is a list | inspect | CRASH AttributeError |
| h09 hashes.json is a list | verify | CRASH AttributeError |
| h10 environment.json without git, rehashed | verify | CRASH KeyError |
| h11 outcome.json without reproducer_name, rehashed | verify | CRASH KeyError |
| h12 reproducer file removed, rehashed | verify | CRASH FileNotFoundError |
| h13 reproducer_name `../missing.py`, rehashed | verify | CRASH FileNotFoundError (the path leaves the bundle) |
| h14 claim.json is a list, rehashed | verify | CRASH AttributeError |
| h15 outcome.json without runs_requested, rehashed | verify | CRASH KeyError |

## Predictions for the change

| case | predicted |
|---|---|
| h01, h02, h03 | exit 1 (hash problem); `invariants: OK` still printed |
| h04, h05 | exit 2, INVALID_BUNDLE (missing hashes.json) |
| h06, h07 | exit 2, INVALID_BUNDLE (hashes.json is not valid JSON) |
| h08, h09 | exit 1 (hashes.json has no files object), no crash |
| h10-h15 | exit 1, VERIFY FAIL, the structure problem named, no crash, nothing started |

- F-035 cases: all 15 keep their results (the F-035 bundles either have `hashes.json` or already fail on an earlier file;
  b02, b03, b10 and b15 now also name `missing hashes.json`, exit code unchanged).
- Unit tests: the existing 131 pass; new tests cover the cases, each structure rule on its own, and `verify` through the CLI
  on a complete synthetic bundle (exit 0, unchanged).
- Real local bundles (14, ignored folders under `labs/jinja-843/`): the 13 complete ones keep `inspect` exit 0 with
  byte-identical output (all show `hashes: OK`) and have no structure problem; `f04_subclass_override` of the first folder
  stays exit 2, its message now `INVALID_BUNDLE: missing outcome.json; missing hashes.json`.

Not covered: Linux and Docker; other malformed values inside `claim.json` (for example a claim object without
`exception_type`), which `evaluate` handles like any user claim.
