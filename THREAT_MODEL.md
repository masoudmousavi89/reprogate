# Threat model (prototype)

Untrusted: the issue text, the investigator/agent, the reproducer, an evidence bundle.

## What this prototype does NOT protect against (read this first)

- **Host execution.** In the default host mode a reproducer runs as a normal process with your user's privileges.
  The static gate is a filter, not a security boundary; a determined author can get around a text filter. Run only
  reproducers you have read. There is no filesystem, network or resource isolation in host mode. The Docker runner
  (Linux, see below) adds isolation but is not a VM-grade boundary; gVisor or a VM is future work.
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

## Round 2 attacks (see `labs/gate-round2/RESULTS.md`)

Hidden dynamic code and raw file writes pass the gate but are stopped later (matcher, tree hash, read-only container).
Known weakness: a builtin callable supplied by the reproducer can fail inside target code and satisfy `type AND location`; only the before/after oracle rejects it.
Update: a message-mismatch attack (a10) no longer matches; `oracle_required` marks bundles that still need the before/after oracle.

Observer split (F-024): closes cheap forgery of the observation file (b01, b03, b04). Still open: a protocol-aware reproducer (b02).
Frame plausibility (F-026): a protocol-aware reproducer must now also name a real file, function and live line of the target (b02 with a fake frame is rejected). Still open: b05, which does exactly that.

Round 3 (F-028, `labs/adversarial-round3/`): in host mode a reproducer can modify installed dependencies and plant a `sitecustomize.py`; neither is detected (the environment fingerprint lists package names and versions, only the repository is content-hashed). Docker mode mounts the repository read-only and a read-only root filesystem; on Linux (F-031) d01-d03 fail there on file permissions of the image (the tool itself detects nothing). A malicious Issue can make a claim that describes intended behaviour; only the before/after oracle rejects it, in host and Docker mode.

`wrong_output` v1 (F-039, EXPERIMENTAL): the verdict comes only from recorded return values of authentic TARGET frames, never from printed output. A reproducer that imitates the observation protocol (w09) is accepted, the same open weakness as b05.

Fresh environment (F-032): with `--env-template` the round-3 attacks that persisted state between runs in host mode (dependency tampering d01, `sitecustomize` d02, poisoned dependency d03) no longer reach the next run, and the template is hash-checked before every copy. Without the flag host mode still shares one environment. A reproducer can still attack the host directly (no sandbox).
