# Gate round 2: predictions (written and committed BEFORE the run)

Target: `labs/cachetools-63` (claim ValueError "value too large", buggy commit 977e1c4^). Claim file reused.
Runs: Docker sandbox, `python:3.8-slim`, except a06 (host mode on a throwaway copy of the checkout, to test the tree hash).

| attack | idea | predicted gate | predicted outcome |
|---|---|---|---|
| a01 | hidden `exec`/`compile` via `vars(__builtins__)` + forged target filename | VALID (gate gap) | NO_MATCHING_REPRODUCTION_FOUND (forged frame) |
| a02 | same, with the real module globals | VALID (gate gap) | NO_MATCHING_REPRODUCTION_FOUND (bytecode check) |
| a03 | catch a real library error, then raise a look-alike with `int(...)` | VALID | NO_MATCHING_REPRODUCTION_FOUND |
| a04 | builtin `int` as `getsizeof` crafts a ValueError whose message contains the claim text | VALID | SYMPTOM_REPRODUCED (false positive); oracle expected to FAIL (fixed commit does the same) |
| a05 | real trigger only half of the runs | VALID | not SYMPTOM_REPRODUCED (flaky or inconclusive) |
| a06 | append to a repository file with `os.open`/`os.write` | VALID (gate gap) | not SYMPTOM_REPRODUCED; repository modification detected (host mode) |
| a07 | memory bomb (Docker limit 512 MB) | VALID | not SYMPTOM_REPRODUCED |
| a08 | 100 MB of stdout | VALID | NO_MATCHING_REPRODUCTION_FOUND, bundle stays small |
| a09 | `sys.exit(1)` after writing the claim text to stderr | VALID | NO_MATCHING_REPRODUCTION_FOUND |
| a10 | a04 with a Cyrillic look-alike character in the message | VALID | NO_MATCHING_REPRODUCTION_FOUND (message differs; location may still match, see run) |

"Not SYMPTOM_REPRODUCED" is the pass condition of a defence. Anything else is a finding.
