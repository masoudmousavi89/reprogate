# Threat model (prototype)

Untrusted: the issue text, the investigator/agent, the reproducer, an evidence bundle.

## What this prototype does NOT protect against (read this first)

- **Host execution.** A reproducer runs as a normal process with your user's privileges. The static gate is
  a filter, not a security boundary; a determined author can get around a text filter. Run only reproducers
  you have read. There is no filesystem, network or resource isolation. A Docker/gVisor runner is future work.
- **In-process observation.** The harness lives in the same Python interpreter as the reproducer. The
  authenticity checks make faking harder, they do not make it impossible. Evidence carries
  `observation_integrity: BEST_EFFORT_IN_PROCESS`. A short, readable reproducer plus a human is part of the
  trust model.
- **Hashes are integrity, not authenticity.** `environment_trust` is always `UNVERIFIED`; bundles are not
  signed and do not carry their environment.
- **Semantic alignment.** A match means "the reported symptom was observed for the recorded anchors", not
  "this is the reported bug". Human review of the benchmark decides how well those two agree.

## What is mechanically checked (and tested on a synthetic library)

`raise` outside a function body (module level, class body, except handlers; F-011); `eval/exec/compile/__import__`; mocking/monkeypatching names and attribute patching of
imported names; `ctypes`, `subprocess`, `sys.settrace`, `os._exit` and friends; file-writing calls; size and
readability limits; fake tracebacks on stdout (ignored); the same exception raised outside target code;
callbacks and subclass overrides that raise from reproducer code; frames with forged filenames/globals;
repository modification during a run (tree hash); hangs (timeout -> INCONCLUSIVE); environment failures.

## Human-only (not detected automatically)

overbroad assertions; unrealistic setup or state; a semantically different bug with the same symptom;
vacuous reproducers (a differential probe is a design item, not implemented here).

## Docker sandbox (`--sandbox docker`, F-017)

Adds: no network, read-only root filesystem and repository, `--cap-drop ALL`, `no-new-privileges`, uid 65534,
memory/cpu/pids limits, tmpfs scratch, container killed on timeout. Does NOT add: a separate observer (the
harness is in the reproducer's process; `/out` is writable), image content verification, protection against
kernel-level container escapes (shared kernel, no gVisor/VM). Tested on Linux only.
