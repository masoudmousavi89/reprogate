"""Mechanical claim provenance: every anchor must occur verbatim in the raw issue body.

An LLM (or a human) may *propose* anchors; only this module decides whether an
anchor is EXACT_QUOTE (found byte-for-byte in the raw body) or INFERRED.
"""
from .util import canonical_json, sha256_bytes

EXACT = "EXACT_QUOTE"
INFERRED = "INFERRED"
REJECTED = "REJECTED"

# Closed vocabulary for REJECTED anchors.
EMPTY_OR_TOO_SHORT = "EMPTY_OR_TOO_SHORT"
AMBIGUOUS = "AMBIGUOUS"
MALFORMED = "MALFORMED"

# Conservative guard (founder decision 2026-09-29), not a semantic claim: an anchor shorter than this
# (after strip) is too weak to count as a quote.
MIN_ANCHOR_CHARS = 3


def _check_anchor(a, body_bytes):
    if not isinstance(a, dict) or not isinstance(a.get("field"), str) or not isinstance(a.get("text"), str):
        field = a.get("field") if isinstance(a, dict) and isinstance(a.get("field"), str) else None
        text = a.get("text") if isinstance(a, dict) and isinstance(a.get("text"), str) else None
        return {"field": field, "text": text, "provenance": REJECTED, "found": False, "reject_reason": MALFORMED}
    item = {"field": a["field"], "text": a["text"]}
    if len(a["text"].strip()) < MIN_ANCHOR_CHARS:
        item.update({"provenance": REJECTED, "found": False, "reject_reason": EMPTY_OR_TOO_SHORT})
        return item
    needle = a["text"].encode("utf-8")
    start = body_bytes.find(needle)
    if start < 0:
        item.update({"provenance": INFERRED, "found": False})
        return item
    count = body_bytes.count(needle)
    if count > 1:
        item.update({"provenance": REJECTED, "found": True, "occurrences": count, "reject_reason": AMBIGUOUS})
        return item
    item.update({"provenance": EXACT, "found": True, "start_byte": start,
                 "end_byte": start + len(needle), "occurrences": 1})
    return item


def check_claim(claim_doc, body_bytes):
    """Return a frozen copy of claim_doc with per-anchor provenance and hashes."""
    doc = dict(claim_doc)
    anchors_out = [_check_anchor(a, body_bytes) for a in claim_doc.get("anchors", [])]
    doc["anchors"] = anchors_out
    issue = dict(doc.get("issue", {}))
    issue["body_sha256"] = sha256_bytes(body_bytes)
    issue["body_bytes"] = len(body_bytes)
    doc["issue"] = issue
    doc["provenance_verified"] = True
    doc["provenance_sufficient"] = _sufficient(anchors_out)
    doc["claim_sha256"] = claim_hash(doc)
    return doc


def _sufficient(anchors):
    ok = {a["field"] for a in anchors if a.get("provenance") == EXACT}
    return "exception_type" in ok and bool(ok & {"message", "location_file"})


def claim_hash(doc):
    """Hash of the claim, its anchor verdicts AND the exact issue snapshot they were checked against."""
    core = {
        "claim": doc.get("claim"),
        "issue_body_sha256": (doc.get("issue") or {}).get("body_sha256"),
        "anchors": [
            {k: a.get(k) for k in ("field", "text", "provenance", "reject_reason", "start_byte", "end_byte")}
            for a in doc.get("anchors", [])
        ],
    }
    return sha256_bytes(canonical_json(core).encode("utf-8"))


def provenance_state(doc, allow_unverified):
    """VERIFIED | INSUFFICIENT | UNVERIFIED_ALLOWED. Raises ValueError if unverified and not allowed."""
    if doc.get("provenance_verified"):
        # F-042: the stored hash is recomputed, and sufficiency comes from the anchors, not from the stored flag.
        stored = doc.get("claim_sha256")
        if not isinstance(stored, str) or stored != claim_hash(doc):
            raise ValueError("claim changed after freezing: claim_sha256 is missing or does not match the claim, "
                             "its anchors and the issue snapshot. Run 'claim-check' again on the raw issue body.")
        return "VERIFIED" if _sufficient(doc.get("anchors", [])) else "INSUFFICIENT"
    if allow_unverified:
        return "UNVERIFIED_ALLOWED"
    raise ValueError(
        "claim provenance was never checked against the raw issue body. Run "
        "'claim-check' first, or pass --allow-unverified-provenance (recorded in the evidence)."
    )
