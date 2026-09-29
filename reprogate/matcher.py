"""Compare one structured observation with the frozen claim (exception kind only)."""
from .constants import RUN_COMPLETED, RUN_ENV_FAILURE
from .util import norm_path

ENV_EXC_TYPES = ("ImportError", "ModuleNotFoundError", "SyntaxError")

# F-033 (founder decision C): a claim message shorter than this (after strip) counts as no message for the matcher.
MIN_MESSAGE_CHARS = 3

# F-012: exceptions the interpreter itself derives from an exception that escaped a generator/coroutine
# (PEP 479). Their traceback holds no frame of the generator's module; the evidence is in the cause.
INTERPRETER_CONVERSIONS = {
    ("RuntimeError", "generator raised StopIteration"): "StopIteration",
    ("RuntimeError", "coroutine raised StopIteration"): "StopIteration",
    ("RuntimeError", "async generator raised StopIteration"): "StopIteration",
    ("RuntimeError", "async generator raised StopAsyncIteration"): "StopAsyncIteration",
}


def _conversion_target_frames(exc):
    """Authentic TARGET frames from the cause of a PEP 479 conversion, or None if it does not apply.

    Only the closed whitelist above qualifies, the conversion must be an explicit cause link, the
    primary exception must not have been raised by a `raise` line of the reproducer, and the cause
    must be of the expected type with an authentic target frame and no forged one.
    """
    want = INTERPRETER_CONVERSIONS.get((exc.get("type"), (exc.get("message") or "").strip()))
    chain = exc.get("chain") or []
    if want is None or not chain or exc.get("raised_by_reproducer_statement", True):
        return None
    cause = chain[0]
    if cause.get("via") != "cause" or cause.get("type") != want:
        return None
    frames = cause.get("frames") or []
    if any(f["class"] == "FORGED_TARGET" for f in frames):
        return None
    target = [f for f in frames if f["class"] == "TARGET"]
    return target or None


def _frame_summary(f, via=None):
    """Evidence-only view of a frame (no absolute paths)."""
    if not f:
        return None
    out = {"index": f.get("index"), "class": f.get("class"), "function": f.get("function"),
           "rel_path": f.get("rel_path")}
    if via:
        out["via"] = via
    return out


def _innermost(frames):
    return max(frames, key=lambda f: f.get("index", -1)) if frames else None


def _loc_match(frame, loc):
    want_file = loc.get("file")
    want_func = loc.get("function")
    if not want_file and not want_func:
        return False
    if want_file and norm_path(frame.get("rel_path") or "") != norm_path(want_file):
        return False
    if want_func and frame.get("function") != want_func:
        return False
    return True


def classify_run(obs, claim):
    """Return a per-run verdict dict.

    Rules (see ARCHITECTURE.md):
      * stdout/stderr are never used; only the harness observation.
      * origin: at least one authentic TARGET frame, no forged target frame, and no
        REPRODUCER frame *after* the first target frame (callback / direct raise / override tricks).
      * match: origin ok AND type equal AND (message contained if the claim has a message, else location matches).
      * an ImportError/SyntaxError in the import phase that is not the claimed symptom is ENV_FAILURE.
    """
    res = {"status": RUN_COMPLETED, "symptom_match": False, "clean_completion": False,
           "reasons": [], "anchors_matched": [], "exception_origin": None, "target_causal_frame": None}
    exc = obs.get("exception")
    if exc is None:
        res["clean_completion"] = obs.get("exit_code") == 0
        res["reasons"].append("NO_EXCEPTION_OBSERVED")
        return res

    frames = exc.get("frames", [])
    res["exception_origin"] = _frame_summary(_innermost(frames))
    target = [f for f in frames if f["class"] == "TARGET"]
    forged = [f for f in frames if f["class"] == "FORGED_TARGET"]
    first_t = min([f["index"] for f in target]) if target else None
    repro_after = first_t is not None and any(
        f["class"] == "REPRODUCER" and f["index"] > first_t for f in frames
    )
    if not target:
        res["reasons"].append("NO_TARGET_FRAME")
    if forged:
        res["reasons"].append("FORGED_TARGET_FRAME")
    if repro_after:
        res["reasons"].append("REPRODUCER_FRAME_AFTER_TARGET")
    origin_ok = bool(target) and not forged and not repro_after
    via_conversion = False
    if not target and not forged:
        via_cause = _conversion_target_frames(exc)
        if via_cause:
            target = via_cause
            origin_ok = True
            via_conversion = True
            res["reasons"] = [r for r in res["reasons"] if r != "NO_TARGET_FRAME"]
            res["reasons"].append("ORIGIN_FROM_INTERPRETER_CONVERSION")

    # F-033: the innermost TARGET frame is the causal frame; `location` is compared only with it (decision A)
    causal = _innermost(target)
    res["target_causal_frame"] = _frame_summary(causal, "interpreter_conversion_cause" if via_conversion else None)
    type_ok = exc.get("type") == claim.get("exception_type")
    want_msg = claim.get("message")
    if want_msg and len(str(want_msg).strip()) < MIN_MESSAGE_CHARS:
        want_msg = None
        res["reasons"].append("MESSAGE_TOO_SHORT_IGNORED")
    msg_ok = bool(want_msg) and want_msg in (exc.get("message") or "")
    loc = claim.get("location") or {}
    loc_ok = bool(causal) and _loc_match(causal, loc)
    if type_ok:
        res["anchors_matched"].append("exception_type")
    else:
        res["reasons"].append("TYPE_MISMATCH")
    if msg_ok:
        res["anchors_matched"].append("message")
    elif want_msg:
        res["reasons"].append("MESSAGE_MISMATCH")
    if loc_ok:
        res["anchors_matched"].append("location")
    elif loc:
        res["reasons"].append("LOCATION_MISMATCH")

    # F-020: when the claim carries a message it must match; location alone is only enough for claims
    # without a message.
    anchor_ok = msg_ok if want_msg else loc_ok
    if origin_ok and type_ok and anchor_ok:
        res["symptom_match"] = True
        return res

    if (exc.get("type") in ENV_EXC_TYPES and obs.get("phase") == "import"
            and claim.get("exception_type") != exc.get("type")):
        res["status"] = RUN_ENV_FAILURE
        res["reasons"].append("IMPORT_PHASE_FAILURE")
    return res
