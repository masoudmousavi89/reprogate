# Roadmap

The scope is kept small on purpose. Architecture changes only with an entry in `findings.md` (see `CONTRIBUTING.md`).
Nothing below is a promise of a date except the pre-registered verdict in `STOP_CRITERIA.md`.

## v0.1 alpha: verifier only

The alpha is the verifier and its evidence. It contains no agent that writes reproducers and uses no LLM or paid API.

Remaining work in the alpha:

- **Claims and provenance:** claims are written by hand or mechanically from the issue text, frozen and hashed before
  the first run of a reproducer, and tied to the raw issue body; show that a claim changed after freezing is rejected.
- **Result schema:** `claim_status` comes from a mechanical check of the claim (supported kind, required fields,
  provenance) instead of a fixed `READY`.
- **Environment:** build the target environment from a read-only wheelhouse without network, record its tree hash
  before the first run and check it before every run; a failing build or import is `ENV_FAILURE`.
- **Fresh checkout of an exact SHA:** `run --checkout-sha` and `oracle --before-sha/--after-sha` evaluate a fresh detached git worktree
  of a full SHA (F-048, Windows). Open: Linux and Docker evidence for this path (`labs/checkout-sha/LINUX_DOCKER_PROMPT.md`), `verify` with a SHA.
- **Reproducer origin:** record whether the reproducer is a verbatim issue snippet, adapted, or written from scratch,
  with a diff and hash for any adaptation. Done (F-043, `--origin-source`, Windows and Linux); a verbatim label must be byte-identical
  to its source. Still open: extracting the snippet from the raw issue body.
- **`wrong_output` on real bugs:** two pilots under protocols committed before the run found no evaluable candidate (F-041,
  F-044); one case study ran end to end on a real bug chosen knowing it fits (F-045). Open: provenance sufficiency is not
  defined for `wrong_output` claims (F-046), and the claim format takes Python literals only. Status stays EXPERIMENTAL.
- **Human-label protocol:** a document that labels claim faithfulness, same-bug alignment and evidence sufficiency
  separately, records disagreements, and names maintainer-only labels a preliminary annotation.
- **Measurement:** the stop / continue verdict is due by 2026-10-13 (`STOP_CRITERIA.md`).

## After the alpha

- An investigator agent that writes reproducers, behind a vendor-neutral interface, and any LLM/API adapter.
- A candidate gate separate from the final verifier, so an agent cannot tune its reproducer against the final check.
- `unexpected_exit` claims.
- Differential reproducer validation (replace the causal frame with a stub; a surviving symptom is a warning sign).
- Automatic claim extraction; `TRACEBACK_QUOTE` / `STRUCTURED_METADATA` provenance; `NEEDS_INFO` claims.
- Reconstruction of historical dependency sets and builds from source.
- Running the human-label protocol with independent labellers, and the second measurement round of `STOP_CRITERIA.md`.
- Kernel-level observation (ptrace, gVisor) instead of in-process observation; signed evidence.
