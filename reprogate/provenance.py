"""Mechanical claim provenance: every anchor must occur verbatim in the raw issue body.

An LLM (or a human) may *propose* anchors; only this module decides whether an
anchor is EXACT_QUOTE (found byte-for-byte in the raw body) or INFERRED.
"""
from .util import canonical_json, sha256_bytes

EXACT = "EXACT_QUOTE"
INFERRED = "INFERRED"


def check_claim(claim_doc, body_bytes):
    """Return a frozen copy of claim_doc with per-anchor provenance and hashes."""
    doc = dict(claim_doc)
    anchors_out = []
    for a in claim_doc.get("anchors", []):
        needle = a["text"].encode("utf-8")
        start = body_bytes.find(needle)
        item = {"field": a["field"], "text": a["text"]}
        if start < 0:
            item.update({"provenance": INFERRED, "found": False})
        else:
            item.update(
                {
                    "provenance": EXACT,
                    "found": True,
                    "start_byte": start,
                    "end_byte": start + len(needle),
                    "occurrences": body_bytes.count(needle),
                }
            )
        anchors_out.append(item)
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
    core = {
        "claim": doc.get("claim"),
        "anchors": [
            {k: a.get(k) for k in ("field", "text", "provenance", "start_byte", "end_byte")}
            for a in doc.get("anchors", [])
        ],
    }
    return sha256_bytes(canonical_json(core).encode("utf-8"))


def provenance_state(doc, allow_unverified):
    """VERIFIED | INSUFFICIENT | UNVERIFIED_ALLOWED. Raises ValueError if unverified and not allowed."""
    if doc.get("provenance_verified"):
        return "VERIFIED" if doc.get("provenance_sufficient") else "INSUFFICIENT"
    if allow_unverified:
        return "UNVERIFIED_ALLOWED"
    raise ValueError(
        "claim provenance was never checked against the raw issue body. Run "
        "'claim-check' first, or pass --allow-unverified-provenance (recorded in the evidence)."
    )
