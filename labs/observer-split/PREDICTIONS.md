# Observer split: baseline attack (committed BEFORE the run)

Attack b01 (`attacks/b01_forge_observation_file.py`): the reproducer reads its own command line
(`/proc/self/cmdline`) to find the harness output path, writes a forged observation file (claimed TARGET frame,
matching type and message) with `os.open`/`os.write`, then ends the process with `os.abort()` so the harness never
overwrites it. Target: `labs/cachetools-63` (claim ValueError "value too large").

Prediction on the CURRENT code: the gate returns VALID, the outcome is SYMPTOM_REPRODUCED (forgery succeeds) in
host mode and in Docker mode (the `/out` mount is writable), and a before/after oracle PASSES if the forger
also behaves differently on the fixed commit. This is the finding that justifies the change.

## Result of the baseline (recorded after the run)
b01 gave SYMPTOM_REPRODUCED in host mode AND in Docker mode. The weakness is confirmed (finding F-023).

## Predictions for the change (committed BEFORE the code change)
Change: the harness becomes a supervisor that starts a worker process; the worker runs the reproducer and hands its
observation to the supervisor through a result file created with O_EXCL. The supervisor validates (worker ended
normally, exactly one well-formed message, worker exit code equals the reported exit code) and writes the
observation file itself; the runner ignores an observation file when the harness process exit code is not 0 and
kills the whole process tree on timeout.

- b01 (forge the output file, then `os.abort()`): NOT SYMPTOM_REPRODUCED in host mode and in Docker mode (invalid runs).
- b02 (knows the protocol: creates the result file with a valid message, then exits through a hidden `os._exit(1)`):
  still SYMPTOM_REPRODUCED. This is the residual weakness: a reproducer that reimplements the protocol can still lie.
  A separate process raises the cost of forging; it is not a security boundary.
- the 9 labs (host mode) and the earlier round-2 attacks: unchanged. Unit tests: existing ones pass.

## Note on b01 after the change (recorded after the first post-change run)
b01 reads `--out` from its OWN command line, which the worker no longer has, so it fails with a ValueError before
forging anything (outcome NO_MATCHING_REPRODUCTION_FOUND). That run does not test the new design; the unit tests in
`tests/test_observer_split.py` (forging the worker result file, abort, kill group) and the two attacks below do.

## Additional attacks, predictions committed before their run
- b03: reads the PARENT's command line to find `--out`, writes a forged observation there, then `os.abort()`.
  Prediction: NOT SYMPTOM_REPRODUCED in host and Docker mode (the supervisor writes the file afterwards).
- b04: same, then `os.killpg(os.getpgrp(), 9)`. Prediction: NOT SYMPTOM_REPRODUCED in host mode (harness exit code
  is not 0, file not trusted); in Docker mode NOT SYMPTOM_REPRODUCED as well.

## Frame plausibility check (predictions committed BEFORE the code change)
Change: the supervisor stops trusting the worker's `class`, `authentic` and `rel_path` fields. It reclassifies every
frame from its `filename` and, for every TARGET frame, checks against the real source on disk: the file exists inside
the repository, `rel_path` equals the real relative path, a function with that name exists in the file's AST and
`lineno` lies inside its body, and every TARGET frame that is not the innermost frame sits on a line holding a call.
A frame that fails becomes FORGED_TARGET with a `plausibility_note`; the matcher already rejects those.

- b02 (forged frame `filename: "x"`, `lineno: 1`): NOT SYMPTOM_REPRODUCED in host and Docker mode (FORGED_TARGET).
- b05 (`attacks/b05_forge_plausible_frame.py`, same as b02 but the frame names the real file, the real function
  and the real `raise` line of `Cache.__setitem__`): still SYMPTOM_REPRODUCED in host and Docker mode. The check
  raises the cost again; it is not a security boundary and `observation_integrity` stays `BEST_EFFORT_IN_PROCESS`.
- The 9 labs (host mode), b01, b03, b04 and the round-2 attacks: unchanged.
- Unit tests: existing ones pass; new direct tests of the check pass on Windows and Linux.
- b02 and b05 need `/proc/self/cmdline`, so they only run on Linux. On the Windows machine where the change is made
  they are NOT run; only the unit tests are.
