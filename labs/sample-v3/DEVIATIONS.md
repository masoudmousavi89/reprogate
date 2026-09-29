# Sample v3: deviations from the measurement protocol (2026-09-29)

The pre-registered texts (`PROTOCOL.md`, `STOP_CRITERIA.md`, `MEASUREMENT-PROTOCOL.md`, `blind-input/`) are not changed.
This file records what happened differently.

1. **Run 0, not blind, not used.** A first attempt-1 session was started in this repository instead of a separate one. It
   had access to files that describe the fixes (for example `CHECKLIST-NARROW.md` on n-43, and the fix commits in
   `draws-narrow.json` and `INSTALL-CHECK-NARROW.md`); whether it read them is unknown. Its outputs are not used. Its branch,
   whose commit carried a tool identity, was deleted from this repository; the files were archived outside the repository.
   The blind attempts were then run in a separate repository with tool access restricted to it (`measure/README.md`).
2. **The maintainer saw a summary of run 0** (which bugs were triggered and how) before any labelling. Any later labelling
   of these scripts would be affected by that.
3. **Human labelling stopped.** Labelling needs a programmer; the maintainer is not one and no independent programmer is
   available. A partial attempt on n-23 used plain-language analogies written by the AI, which makes the labels depend on
   the AI's framing; those partial labels are discarded and not used. M1/M2 stay INCONCLUSIVE (n = 6 < 10) and no result
   is derived from the 18 scripts.
4. **Model independence.** The blind sessions used a model of the same family that helped design the tool.
