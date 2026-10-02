"""Claim kinds (F-039): which claims the tool supports, and the parts of a `wrong_output` claim.

`exception` is the version-0 claim kind. `wrong_output` is EXPERIMENTAL (labs/wrong-output/DESIGN.md). Any other kind is
UNSUPPORTED; before F-039 the kind was not checked at all.
"""
import ast

KIND_EXCEPTION = "exception"
KIND_WRONG_OUTPUT = "wrong_output"
MATURITY = {KIND_EXCEPTION: "STABLE_V0", KIND_WRONG_OUTPUT: "EXPERIMENTAL"}

READY = "READY"
UNSUPPORTED = "UNSUPPORTED"


def kind(claim):
    """A claim without a kind is an exception claim (all claims written before F-039)."""
    return (claim or {}).get("kind") or KIND_EXCEPTION


def parse_literal(text):
    """(True, value) if `text` is a Python literal (numbers, strings, bytes, booleans, None and containers of them)."""
    if not isinstance(text, str) or not text.strip():
        return False, None
    try:
        return True, ast.literal_eval(text.strip())
    except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
        return False, None


def watch_target(claim):
    """(file, function) of a `wrong_output` claim's target, else None."""
    t = (claim or {}).get("target")
    if not isinstance(t, dict):
        return None
    f, fn = t.get("file"), t.get("function")
    if isinstance(f, str) and f.strip() and isinstance(fn, str) and fn.strip():
        return f.strip().replace("\\", "/"), fn.strip()
    return None


def _exception_fields(claim):
    """Required fields of an exception claim (req_003): None when fine, else a one-sentence reason."""
    t = claim.get("exception_type")
    if not isinstance(t, str) or not t.strip():
        return "exception claim needs exception_type as a non-empty string"
    if claim.get("message") is not None and not isinstance(claim["message"], str):
        return "exception claim: message must be a string when given"
    loc = claim.get("location")
    if loc is not None:
        if not isinstance(loc, dict):
            return "exception claim: location must be an object when given"
        for part in ("file", "function"):
            if part in loc and (not isinstance(loc[part], str) or not loc[part].strip()):
                return "exception claim: location.%s must be a non-empty string when given" % part
    return None


def support(claim):
    """READY or UNSUPPORTED for the tool as it is, with a short note."""
    if not isinstance(claim, dict):
        return UNSUPPORTED, "claim is not an object"
    k = kind(claim)
    if k == KIND_EXCEPTION:
        problem = _exception_fields(claim)
        return (UNSUPPORTED, problem) if problem else (READY, None)
    if k != KIND_WRONG_OUTPUT:
        return UNSUPPORTED, "claim kind %r is not supported" % (k,)
    if watch_target(claim) is None:
        return UNSUPPORTED, "wrong_output claim needs target.file and target.function"
    inp = claim.get("input")
    if not isinstance(inp, str) or not inp.strip():
        return UNSUPPORTED, "wrong_output claim needs the input as the issue states it"
    for part in ("expected", "actual"):
        if not parse_literal(claim.get(part))[0]:
            return UNSUPPORTED, "wrong_output claim: %s is not a Python literal" % part
    ok_e, e = parse_literal(claim.get("expected"))
    ok_a, a = parse_literal(claim.get("actual"))
    if _same(e, a):
        return UNSUPPORTED, "wrong_output claim: expected and actual are equal"
    return READY, None


def _same(x, y):
    try:
        return type(x) == type(y) and x == y
    except Exception:
        return False


def value_equals(observed_repr, claim_text):
    """Compare a recorded repr with a claim literal: by value when both are literals, else by exact text."""
    ok_c, want = parse_literal(claim_text)
    ok_o, got = parse_literal(observed_repr)
    if ok_c and ok_o:
        return _same(got, want)
    return isinstance(observed_repr, str) and isinstance(claim_text, str) and observed_repr.strip() == claim_text.strip()
