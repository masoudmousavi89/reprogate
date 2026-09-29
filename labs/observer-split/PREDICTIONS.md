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
