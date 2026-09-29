# Observer split: baseline attack (committed BEFORE the run)

Attack b01 (`attacks/b01_forge_observation_file.py`): the reproducer reads its own command line
(`/proc/self/cmdline`) to find the harness output path, writes a forged observation file (claimed TARGET frame,
matching type and message) with `os.open`/`os.write`, then ends the process with `os.abort()` so the harness never
overwrites it. Target: `labs/cachetools-63` (claim ValueError "value too large").

Prediction on the CURRENT code: the gate returns VALID, the outcome is SYMPTOM_REPRODUCED (forgery succeeds) in
host mode and in Docker mode (the `/out` mount is writable), and a before/after oracle PASSES if the forger
also behaves differently on the fixed commit. This is the finding that justifies the change.
