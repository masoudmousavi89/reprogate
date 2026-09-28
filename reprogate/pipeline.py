"""Orchestration: gate -> environment freeze -> repeated fresh runs -> match -> outcome -> evidence."""
import os
import shutil
import tempfile

from . import SCHEMA_VERSION, __version__
from . import constants as C
from .evidence import verify_hashes, write_hashes
from .gate import gate_source
from .matcher import classify_run
from .outcome import aggregate
from .provenance import provenance_state
from . import sandbox as sbx
from .runner import (capture_environment, env_names, git_info, run_once, tree_hash)
from .util import now_utc, read_json, sha256_bytes, write_json



def _run_record(index, raw, claim, tree_before, tree_after_hash):
    rec = {"index": index, "seed": raw["seed"], "duration_s": raw.get("duration_s"),
           "exit_code": None, "status": None, "symptom_match": False, "clean_completion": False,
           "reasons": [], "invalid_reason": None}
    if raw["launch_error"]:
        rec["status"] = C.RUN_ENV_FAILURE
        rec["reasons"].append("INTERPRETER_LAUNCH_FAILED")
        return rec
    if tree_after_hash != tree_before:
        rec["status"] = C.RUN_INVALID
        rec["invalid_reason"] = C.REPOSITORY_MODIFIED
        return rec
    if raw["timed_out"]:
        rec["status"] = C.RUN_TIMEOUT
        return rec
    obs = raw["observation"]
    if obs is None:
        rec["status"] = C.RUN_INVALID
        err = (raw["stderr"] or b"").decode("utf-8", "replace")
        rec["invalid_reason"] = "HARNESS_ERROR" if ("harness.py" in err or raw["returncode"] == 70) else "OBSERVATION_MISSING"
        rec["reasons"].append(raw["observation_error"] or "")
        return rec
    verdict = classify_run(obs, claim)
    rec.update({k: verdict[k] for k in ("status", "symptom_match", "clean_completion", "reasons")})
    rec["anchors_matched"] = verdict["anchors_matched"]
    rec["exit_code"] = obs.get("exit_code")
    rec["phase"] = obs.get("phase")
    return rec


def evaluate(repo, python, claim_doc, repro_path, out_dir, runs=5, timeout=30, min_completed=3,
             gate=True, allow_unverified_provenance=False, origin="AGENT_ADAPTED", attempts=0,
             base_seed=1000, pythonpath_extra=None, sandbox=None):
    """Evaluate one reproducer against one checkout. Returns the outcome dict (also written to out_dir)."""
    prov = provenance_state(claim_doc, allow_unverified_provenance)  # may raise ValueError
    os.makedirs(out_dir, exist_ok=True)
    with open(repro_path, "rb") as f:
        repro_bytes = f.read()
    repro_name = os.path.basename(repro_path)
    os.makedirs(os.path.join(out_dir, "reproducer"), exist_ok=True)
    with open(os.path.join(out_dir, "reproducer", repro_name), "wb") as f:
        f.write(repro_bytes)
    write_json(os.path.join(out_dir, "claim.json"), claim_doc)

    if gate:
        gate_res = gate_source(repro_bytes)
    else:
        gate_res = {"status": C.GATE_VALID, "reproducer_sha256": sha256_bytes(repro_bytes), "findings": [],
                    "note": "GATE_SKIPPED_BY_CALLER (tests only)"}
    write_json(os.path.join(out_dir, "gate.json"), gate_res)

    env_info, env_sha = capture_environment(python, sandbox)
    sandbox_rec = sbx.record(sandbox)
    git = git_info(repo)
    tree_before, n_files = tree_hash(repo)
    write_json(os.path.join(out_dir, "environment.json"), {
        "interpreter": env_info, "environment_sha256": env_sha, "git": git,
        "repository_tree_sha256_before": tree_before, "repository_files_hashed": n_files,
        "environment_variables_allowed": env_names(), "sandbox": sandbox_rec,
        "environment_trust": "UNVERIFIED",
    })

    run_records = []
    if gate_res["status"] == C.GATE_VALID and env_info["python"] is not None:
        for i in range(runs):
            run_dir = os.path.join(out_dir, "runs", "run-%02d" % (i + 1))
            raw = run_once(python, repo, repro_bytes, run_dir, timeout, base_seed + i * 7919, pythonpath_extra, sandbox)
            after, _ = tree_hash(repo)
            rec = _run_record(i + 1, raw, claim_doc["claim"], tree_before, after)
            write_json(os.path.join(run_dir, "run.json"), rec)
            run_records.append(rec)
    elif gate_res["status"] == C.GATE_VALID:
        run_records = [{"index": i + 1, "seed": None, "status": C.RUN_ENV_FAILURE, "symptom_match": False,
                        "clean_completion": False, "reasons": ["INTERPRETER_LAUNCH_FAILED"],
                        "invalid_reason": None} for i in range(runs)]

    agg = aggregate(run_records, min_completed=min_completed, provenance=prov,
                    reproducer_status=gate_res["status"])
    outcome = {
        "schema_version": SCHEMA_VERSION, "tool_version": __version__, "created_at": now_utc(),
        "outcome": agg["outcome"], "outcome_reason": agg["outcome_reason"],
        "outcome_qualifier": agg["outcome_qualifier"],
        "claim_status": "READY", "reproducer_status": gate_res["status"],
        "run_status": [r["status"] for r in run_records], "counts": agg["counts"],
        "min_completed": min_completed, "runs_requested": runs,
        "reproducer_origin": origin, "attempts_before_submission": attempts,
        "claim_faithfulness": "NOT_REVIEWED", "observation_integrity": C.OBSERVATION_INTEGRITY,
        "environment_trust": "UNVERIFIED", "claim_provenance": prov, "sandbox": sandbox_rec,
        "repository": {"commit": git["commit"], "tree_sha256_before": tree_before},
        "environment_sha256": env_sha, "reproducer_name": repro_name,
        "reproducer_sha256": gate_res["reproducer_sha256"], "claim_sha256": claim_doc.get("claim_sha256"),
    }
    write_json(os.path.join(out_dir, "outcome.json"), outcome)
    write_hashes(out_dir)
    return outcome


def replay(bundle, repo, python, runs=None, timeout=30, sandbox=None):
    """Re-run a bundle's reproducer and compare with the recorded outcome. Never trusts bundle code blindly:
    the reproducer goes through the gate again and runs in fresh processes."""
    ok, problems = verify_hashes(bundle)
    report = {"hashes_ok": ok, "problems": problems, "replay_outcome": None, "same_outcome": None}
    if not ok:
        return report
    rec = read_json(os.path.join(bundle, "outcome.json"))
    env = read_json(os.path.join(bundle, "environment.json"))
    claim = read_json(os.path.join(bundle, "claim.json"))
    repro = os.path.join(bundle, "reproducer", rec["reproducer_name"])
    report["recorded_outcome"] = [rec["outcome"], rec["outcome_reason"]]
    now_commit = git_info(repo)["commit"]
    report["commit_matches"] = (env["git"]["commit"] == now_commit) if env["git"]["commit"] else None
    _, now_env_sha = capture_environment(python, sandbox)
    report["environment_matches"] = (now_env_sha == env.get("environment_sha256"))
    tmp = tempfile.mkdtemp(prefix="reprogate-verify-")
    try:
        new = evaluate(repo, python, claim, repro, os.path.join(tmp, "replay"),
                       runs=runs or rec["runs_requested"], timeout=timeout,
                       min_completed=rec["min_completed"], allow_unverified_provenance=True,
                       origin=rec["reproducer_origin"], attempts=rec["attempts_before_submission"], sandbox=sandbox)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    report["replay_outcome"] = [new["outcome"], new["outcome_reason"]]
    report["same_outcome"] = report["replay_outcome"] == report["recorded_outcome"]
    return report


def oracle(before_repo, after_repo, python, claim_doc, repro_path, out_dir, after_python=None, **kw):
    """Before/after-fix oracle: the same reproducer must reproduce the symptom before the fix and
    complete CLEANLY after it ('no longer matches' is not enough: an ImportError is not a fix)."""
    before = evaluate(before_repo, python, claim_doc, repro_path, os.path.join(out_dir, "before"), **kw)
    after = evaluate(after_repo, after_python or python, claim_doc, repro_path, os.path.join(out_dir, "after"), **kw)
    ac = after["counts"]
    if ac["total"] and ac["clean_completion_runs"] == ac["total"] and ac["completed"] == ac["total"]:
        post = "CLEAN_COMPLETION"
    elif ac["total"] and ac["env_failures"] == ac["total"]:
        post = "ENV_FAILURE"
    elif ac["matching"] > 0:
        post = "STILL_FAILS"
    else:
        post = "OTHER_NON_CLEAN"
    res = {
        "before_outcome": [before["outcome"], before["outcome_reason"]],
        "after_outcome": [after["outcome"], after["outcome_reason"]],
        "post_fix_classification": post,
        "oracle_pass": before["outcome"] == C.SYMPTOM_REPRODUCED and post == "CLEAN_COMPLETION",
        "note": "fail-to-pass is a necessary helper oracle, not ground truth",
        "created_at": now_utc(),
    }
    write_json(os.path.join(out_dir, "oracle.json"), res)
    return res
