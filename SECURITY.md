# Security policy

ReproGate is an experimental prototype. Only the latest commit on `main` is supported; there are no releases yet.

## Read this before running anything

ReproGate is **not a security boundary**. In the default host mode a reproducer runs as a normal process with your
user's privileges, with no filesystem, network or resource isolation. The static gate is a filter, not a sandbox.
`--sandbox docker` (Linux) adds a network-less, read-only container, but no protection against kernel-level container
escapes. Run only reproducers and evidence bundles you have read. Details: `THREAT_MODEL.md`.

## What to report privately

Problems that can harm the person running the tool, for example:

- a way to make `verify` or `inspect` execute code from an evidence bundle on the host without
  `--allow-host-execution`;
- a path in a bundle that makes the tool read or write files outside the bundle or the output folder;
- `--sandbox docker` starting a container with network access, a writable repository or extra privileges;
- secrets or personal data leaking into evidence bundles.

Please use GitHub's private vulnerability reporting (the **Security** tab of this repository, "Report a
vulnerability") and do not open a public issue for these. Include the commit, your OS and Python version, and the
smallest input that shows the problem. This is a one-person project; expect an answer within a few days, not hours.

## What can be reported publicly

Ways to get a wrong verdict are not security vulnerabilities here; they are the most useful bug reports. A reproducer
that gets `SYMPTOM_REPRODUCED` without really triggering the bug, a correct reproducer that is rejected, or a forged
observation that is accepted: open a normal issue. The known open cases are listed in `THREAT_MODEL.md`
(for example b05, a reproducer that imitates the observation protocol with a real file, function and line).
