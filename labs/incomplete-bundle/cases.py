"""Incomplete and unreadable bundles for inspect and verify (F-035). No reproducer is executed.

Usage (repo root): py -3.8 labs/incomplete-bundle/cases.py
Each case builds a synthetic bundle in a temporary folder and calls the CLI in-process. Every verify case fails before
any replay (missing file, bad JSON, hash problem, invariant violation or missing host flag), so nothing runs.
Prints one line per case: id | command | exit code or CRASH <exception type> | INVALID_BUNDLE if stderr carries it.
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from reprogate import cli  # noqa: E402
from reprogate import constants as C  # noqa: E402
from reprogate.evidence import write_hashes  # noqa: E402
from reprogate.outcome import aggregate  # noqa: E402


def valid_outcome():
    runs = [{"status": C.RUN_COMPLETED, "symptom_match": True, "clean_completion": False, "invalid_reason": None}] * 5
    agg = aggregate(runs, min_completed=3, provenance="VERIFIED", reproducer_status=C.GATE_VALID, claim_status="READY")
    return {"outcome": agg["outcome"], "outcome_reason": agg["outcome_reason"],
            "outcome_qualifier": agg["outcome_qualifier"], "claim_status": "READY",
            "reproducer_status": C.GATE_VALID, "run_status": [r["status"] for r in runs], "counts": agg["counts"],
            "min_completed": 3, "runs_requested": 5, "claim_provenance": "VERIFIED", "oracle_required": True,
            "reproducer_name": "r.py", "reproducer_origin": "HUMAN_AUTHORED", "attempts_before_submission": 0,
            "observation_integrity": "BEST_EFFORT_IN_PROCESS", "environment_trust": "HOST",
            "sandbox": {"kind": "none"}}


def write(path, doc):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f)


def full(d, hashes=True):
    os.makedirs(os.path.join(d, "reproducer"))
    with open(os.path.join(d, "reproducer", "r.py"), "w") as f:
        f.write("print('never executed')\n")
    write(os.path.join(d, "claim.json"), {"claim": {"kind": "exception", "exception_type": "IndexError"}})
    write(os.path.join(d, "gate.json"), {"status": C.GATE_VALID})
    write(os.path.join(d, "environment.json"), {"git": {"commit": None}, "environment_sha256": "0" * 64})
    write(os.path.join(d, "outcome.json"), valid_outcome())
    if hashes:
        write_hashes(d)
    return d


def real_shape(d):
    # the shape of the interrupted f04_subclass_override folder: claim, gate and reproducer only
    full(d, hashes=False)
    os.remove(os.path.join(d, "outcome.json"))
    os.remove(os.path.join(d, "environment.json"))
    return d


def delete_after_hashing(name):
    def build(d):
        full(d)
        os.remove(os.path.join(d, name))
        return d
    return build


def delete_and_rehash(name):
    def build(d):
        full(d)
        os.remove(os.path.join(d, name))
        write_hashes(d)
        return d
    return build


def truncate(name, rehash):
    def build(d):
        full(d)
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write('{"outcome": "SYMPT')
        if rehash:
            write_hashes(d)
        return d
    return build


def outcome_as(doc):
    def build(d):
        full(d)
        write(os.path.join(d, "outcome.json"), doc)
        write_hashes(d)
        return d
    return build


def without_sandbox(d):
    o = valid_outcome()
    del o["sandbox"]
    return outcome_as(o)(d)


def tampered(d):
    o = valid_outcome()
    o["outcome_reason"] = C.INSUFFICIENT_VALID_RUNS  # SYMPTOM_REPRODUCED cannot carry this reason
    return outcome_as(o)(d)


def empty(d):
    os.makedirs(d)
    return d


def absent(d):
    return d


VERIFY = ["--repo", ROOT, "--python", sys.executable]
CASES = [
    ("b01_path_absent", "inspect", absent, []),
    ("b02_empty_folder", "inspect", empty, []),
    ("b03_real_shape_incomplete", "inspect", real_shape, []),
    ("b04_outcome_deleted_after_hashing", "inspect", delete_after_hashing("outcome.json"), []),
    ("b05_outcome_not_json", "inspect", truncate("outcome.json", rehash=False), []),
    ("b06_outcome_is_a_list", "inspect", outcome_as([1, 2]), []),
    ("b07_outcome_without_sandbox", "inspect", without_sandbox, []),
    ("b08_complete_valid", "inspect", full, []),
    ("b09_tampered_rehashed", "inspect", tampered, []),
    ("b10_real_shape_incomplete", "verify", real_shape, VERIFY + ["--allow-host-execution"]),
    ("b11_outcome_deleted_after_hashing", "verify", delete_after_hashing("outcome.json"),
     VERIFY + ["--allow-host-execution"]),
    ("b12_claim_deleted_and_rehashed", "verify", delete_and_rehash("claim.json"), VERIFY + ["--allow-host-execution"]),
    ("b13_environment_not_json_rehashed", "verify", truncate("environment.json", rehash=True),
     VERIFY + ["--allow-host-execution"]),
    ("b14_tampered_rehashed", "verify", tampered, VERIFY + ["--allow-host-execution"]),
    ("b15_real_shape_no_host_flag", "verify", real_shape, VERIFY),
]


def run_case(cid, cmd, build, extra):
    tmp = tempfile.mkdtemp(prefix="reprogate-f035-")
    try:
        bundle = build(os.path.join(tmp, "bundle"))
        out, err = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = cli.main([cmd, "--evidence", bundle] + extra)
            result = "exit %s" % code
        except Exception as e:  # the baseline crashes here; a real process would print a traceback and exit 1
            result = "CRASH %s" % type(e).__name__
        tag = "INVALID_BUNDLE" if "INVALID_BUNDLE" in err.getvalue() else "-"
        return "%-36s | %-7s | %-26s | %s" % (cid, cmd, result, tag)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    for c in CASES:
        print(run_case(*c))
