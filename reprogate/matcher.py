"""Compare one structured observation with the frozen claim (exception kind only)."""
from .constants import RUN_COMPLETED, RUN_ENV_FAILURE
from .util import norm_path

ENV_EXC_TYPES = ("ImportError", "ModuleNotFoundError", "SyntaxError")


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
      * match: origin ok AND type equal AND (message contained OR location matches).
      * an ImportError/SyntaxError in the import phase that is not the claimed symptom is ENV_FAILURE.
    """
    res = {"status": RUN_COMPLETED, "symptom_match": False, "clean_completion": False,
           "reasons": [], "anchors_matched": []}
    exc = obs.get("exception")
    if exc is None:
        res["clean_completion"] = obs.get("exit_code") == 0
        res["reasons"].append("NO_EXCEPTION_OBSERVED")
        return res

    frames = exc.get("frames", [])
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

    type_ok = exc.get("type") == claim.get("exception_type")
    want_msg = claim.get("message")
    msg_ok = bool(want_msg) and want_msg in (exc.get("message") or "")
    loc = claim.get("location") or {}
    loc_ok = any(_loc_match(f, loc) for f in target)
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

    if origin_ok and type_ok and (msg_ok or loc_ok):
        res["symptom_match"] = True
        return res

    if (exc.get("type") in ENV_EXC_TYPES and obs.get("phase") == "import"
            and claim.get("exception_type") != exc.get("type")):
        res["status"] = RUN_ENV_FAILURE
        res["reasons"].append("IMPORT_PHASE_FAILURE")
    return res
