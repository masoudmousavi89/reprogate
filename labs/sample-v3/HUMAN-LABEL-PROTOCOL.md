# Human-label protocol, three dimensions (req_018; pre-registered 2026-10-03, before any label is written under it)

Scope: this is a PROTOCOL only (decision_067, decision_072). No label is produced under it now; the labelling of the NARROW sample is
stopped because no independent programmer is available. Nothing here changes `STOP_CRITERIA.md` or `MEASUREMENT-PROTOCOL.md`; it
complements the latter, which has only a binary CORRECT / INCORRECT label for reproducers, and it is the "req_018 protocol" that metric M3 of
`STOP_CRITERIA.md` refers to. A change to this file needs a new dated section that states why; labels already written are reported against the
version in force when they were written.

Why three dimensions: one verdict word hides which part failed. A reproducer can be faithful to the claim and still hit another bug; a claim can
be unfaithful to the report while the bundle is perfectly sufficient as evidence. They are labelled separately and never merged into one score.

## 1. The three dimensions (values from decision_020; the sufficiency definition is new and operational)

### 1.1 Claim faithfulness: does the frozen claim say what the report says?
Subject: `claim.json` (claim fields and anchors) against the report body (the raw bytes whose sha256 the claim carries). The reproducer and every
tool output are NOT shown.
- `FAITHFUL`: every field of the claim (type, message, location, or for `wrong_output` input / expected / actual) is what the report states, nothing
  is added or dropped that changes the meaning.
- `PARTIALLY_FAITHFUL`: the claim is a correct subset or a harmless generalisation (for example the type and location are right, the message is
  shortened to a substring that still appears in the report), or one field is right and another is missing.
- `UNFAITHFUL`: a field contradicts the report or states a different failure (wrong type, a message from another traceback in the same report,
  a location the report does not name).
- `INSUFFICIENT_EVIDENCE`: the report is too vague to decide (no traceback, no stated expected or actual value).

### 1.2 Same-bug alignment: does the reproducer trigger the reported bug for the reported reason?
Subject: the report, the affected checkout, `repro.py`, and the raw output of one run of it (`run.txt`). The fix diff and every ReproGate output are NOT
shown (same order as `MEASUREMENT-PROTOCOL.md` section 2: report -> reproducer -> label -> freeze -> fix diff -> tool).
- `SAME_REPORTED_BUG`: the failure the reproducer triggers is the failure the report describes, through the code path the report describes.
- `RELATED_BUT_NOT_SAME`: it fails in the same area or with the same exception type, but the cause or path is different (for example the same
  exception raised by a different argument, or by a user callback).
- `UNRELATED_FAILURE`: it fails for another reason (import error, wrong usage, a bug unrelated to the report), or it does not fail.
- `INSUFFICIENT_EVIDENCE`: the reviewer cannot decide with the material shown (record what was missing).

### 1.3 Evidence sufficiency: is the evidence bundle enough to support the verdict it carries?
This is judged on the bundle, mechanically where possible, so two reviewers get the same answer. The reviewer fills seven yes/no items; each item names the
file or command that answers it. The label follows from the items by a fixed rule.

| item | question | where it is read |
|---|---|---|
| E1 | Is the claim provenance VERIFIED against the raw issue body (not `UNVERIFIED_ALLOWED`, not `INSUFFICIENT`)? | `outcome.json` `claim_provenance`, `inspect` |
| E2 | Does the reproducer origin carry evidence (`IDENTICAL_TO_SOURCE` or `SOURCE_AND_DIFF`, with the recorded hashes), not `NONE`? | `outcome.json` `reproducer_origin_evidence` |
| E3 | Did at least `min_completed` runs complete, and is there no `INVALID` run and no `TIMEOUT` run? | `outcome.json` `counts`, `run_status` |
| E4 | Is the outcome backed by a passing before/after oracle (before `SYMPTOM_REPRODUCED`, after clean completion), both bundles present? | `oracle.json` (a `SYMPTOM_REPRODUCED` outcome without an oracle bundle answers NO) |
| E5 | Does `environment.json` hold the environment hash, the repository tree hash, and a `git.commit` equal to the claim's target SHA? | `environment.json`, `claim.json` |
| E6 | Do `hashes.json` and the cross-field invariants verify? | `reprogate inspect` (exit code 0) |
| E7 | Does an independent replay agree (`verify` PASS in a sandbox, by someone other than the person who produced the bundle)? | `reprogate verify` |

Rule: `SUFFICIENT` if E1 to E7 are all YES. `INSUFFICIENT` if any is NO (the failing items are recorded). `NOT_APPLICABLE` if the outcome is
`NOT_EVALUATED` (there is no verdict to support). A bundle with outcome `NO_MATCHING_REPRODUCTION_FOUND` or `INCONCLUSIVE` is judged with the same items,
except that E4 is YES when the oracle was not required (`oracle_required: false`). The reviewer may add free text but may not change the rule.
Sufficiency says nothing about whether the claim or the reproducer is right (1.1 and 1.2 do).

## 2. Reviewers
- Ideal: two independent human reviewers who can read Python and the target project's code, are not the maintainer of this tool, label blind to each
  other and to every tool output, and are given the items in a different random order each (the order and its seed are recorded).
- If only the founder and the AI are available the result is called **preliminary annotation**, in every table and sentence that uses it. The AI
  assembles sheets and checks formats; it does not label, because an AI label presented as a human label would remove the independence the
  protocol exists for (decision_067).
- A reviewer who wrote or tuned the reproducer, or who built the tool, is not an independent reviewer for that item.

## 3. Label sheet and recording
One JSON object per (item, dimension, reviewer), committed before the fix diff or any tool output is shown for that item, and never edited afterwards (a
wrong-looking label is reported, not changed):
`{"item": "<id>", "dimension": "claim_faithfulness|same_bug|evidence_sufficiency", "reviewer": "<id>", "label": "<value>", "items_E1_E7": {"E1": true, ...}, "missing": "<text or null>", "time_spent_minutes": <n>, "seen": ["report", "claim.json"], "created_at": "<UTC>"}`
(`items_E1_E7` only for sufficiency). The sheet states which files the reviewer was shown; that list is part of the record.

## 4. Disagreement and adjudication
- Disagreements are counted per dimension (exact label match; `INSUFFICIENT_EVIDENCE` counts as a label, not as a missing value). With two reviewers
  report raw agreement and Cohen's kappa per dimension, together with n. With fewer than 20 items per dimension kappa is reported but no
  reliability claim is made from it (consistent with decision_020: a development corpus of 10 to 15 items is not a reliability proof).
- Adjudication: the two reviewers discuss only the items on which they differ, in writing, without the tool output; if they still differ, a third
  independent reviewer decides; if there is none, the item stays `UNADJUDICATED` and is excluded from every denominator that needs a single label
  (it is still listed). The original labels are kept next to the final one.
- With a single reviewer there is no disagreement data; say so and use "preliminary annotation".

## 5. Denominators (stated before any number exists)
- False Reproduction Rate: human-reviewed positives, that is items whose tool outcome is `SYMPTOM_REPRODUCED` or `SYMPTOM_REPRODUCED_FLAKY` and that
  have a final same-bug label. False reproductions = those whose final label is not `SAME_REPORTED_BUG`. The denominator is NOT the number of issues
  or the number of reproducers (decision_020).
- Agreement with the tool (metric M3): per dimension, items with a final label that is not `INSUFFICIENT_EVIDENCE`; the numerator is the items where the
  tool's verdict maps to the same side (tool positive and `SAME_REPORTED_BUG`, or tool not positive and any other final same-bug label). Items labelled
  `INSUFFICIENT_EVIDENCE` or `UNADJUDICATED` are excluded from the agreement denominator and reported as a count next to it.
- Every table states n, the number of reviewers, whether the labels are independent or a preliminary annotation, and the date of this protocol version.
- No accuracy, precision or reliability figure is published before a BUILD verdict (`STOP_CRITERIA.md`, public claims).

## 6. What this protocol does not do
It does not label anything now; it does not make the tool's verdict a label; it does not decide the stop / continue verdict; it does not turn
evidence sufficiency into a claim that the bug is real (sufficiency is about the bundle). Running it needs at least one independent programmer, which is
not available (decision_067). A third reviewer for adjudication is optional and not available either.
