"""Orchestration: gate -> environment freeze -> repeated fresh runs -> match -> outcome -> evidence."""
import difflib
import os
import shutil
import tempfile
import time

from . import SCHEMA_VERSION, __version__
from . import claims
from .checkout import Checkout
from . import constants as C
from .evidence import verify_hashes, write_hashes
from .gate import gate_source
from .invariants import validate_outcome
from .matcher import classify_run
from .outcome import aggregate
from .provenance import provenance_state
from . import sandbox as sbx
from .runner import (capture_environment, env_names, git_info, run_once, tree_hash)
from .util import now_utc, read_json, sha256_bytes, write_json



ENV_FRESH = "FRESH_COPY_PER_RUN"
ENV_SHARED = "SHARED_HOST_ENVIRONMENT"


def _prepare_template(env_template, python, sandbox):
    """F-032: validate --env-template (host mode only, python inside it) and take its tree hash."""
    if not env_template:
        return None
    if sandbox is not None:
        raise ValueError("--env-template is for host mode; Docker already gives every run a fresh container")
    root = os.path.abspath(env_template)
    if not os.path.isdir(root):
        raise ValueError("--env-template is not a directory: %s" % env_template)
    rel = os.path.relpath(os.path.abspath(python), root)
    if rel.startswith("..") or os.path.isabs(rel):
        raise ValueError("--python must live inside --env-template")
    sha, files = tree_hash(root)
    return {"root": root, "rel": rel, "sha": sha, "files": files}


def _fresh_copy(template):
    """Copy the template to a temp directory outside the evidence bundle; the template must be unchanged."""
    now, _ = tree_hash(template["root"])
    if now != template["sha"]:
        raise ValueError("environment template changed during the evaluation (tree hash differs); aborting")
    holder = tempfile.mkdtemp(prefix="reprogate-env-")
    start = time.time()
    shutil.copytree(template["root"], os.path.join(holder, "env"), symlinks=True)
    return os.path.join(holder, "env", template["rel"]), holder, round(time.time() - start, 3)


def _anchor_states(claim_doc):
    """F-033 (decision B): evidence only. Which anchors are EXACT_QUOTE and the state of the others."""
    verified, not_verified = [], {}
    for a in claim_doc.get("anchors") or []:
        field = a.get("field") if isinstance(a, dict) else None
        if not field:
            continue
        if a.get("provenance") == "EXACT_QUOTE":
            verified.append(field)
        else:
            not_verified[field] = a.get("reject_reason") or a.get("provenance") or "UNVERIFIED"
    return sorted(verified), dict(sorted(not_verified.items()))


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
    rec.update({k: verdict[k] for k in ("status", "symptom_match", "clean_completion", "reasons",
                                        "exception_origin", "target_causal_frame")})
    rec["anchors_matched"] = verdict["anchors_matched"]
    rec["exit_code"] = obs.get("exit_code")
    rec["phase"] = obs.get("phase")
    return rec


ORIGIN_VERBATIM = "ISSUE_VERBATIM_SNIPPET"
ORIGIN_ADAPTED = "AGENT_ADAPTED"


def _origin_evidence(origin, origin_source, repro_bytes, repro_name):
    """F-043: what the origin label is backed by. Returns (evidence, source bytes or None, diff bytes or None).
    A verbatim snippet must be byte-identical to the supplied source; an adaptation keeps the source and a diff."""
    src = None
    if origin_source is not None:
        with open(origin_source, "rb") as f:
            src = f.read()
    if origin == ORIGIN_VERBATIM:
        if src is None:
            raise ValueError("origin ISSUE_VERBATIM_SNIPPET needs --origin-source (the text the reproducer is copied from)")
        if src != repro_bytes:
            raise ValueError("origin ISSUE_VERBATIM_SNIPPET requires the reproducer to be byte-identical to "
                             "--origin-source; it is not (use AGENT_ADAPTED for an adapted snippet)")
        return "IDENTICAL_TO_SOURCE", src, None
    if origin == ORIGIN_ADAPTED:
        if src is None:
            return "NONE", None, None  # an adaptation with no recorded source: allowed, recorded as not documented
        diff = "".join(difflib.unified_diff(
            src.decode("utf-8", "replace").splitlines(True), repro_bytes.decode("utf-8", "replace").splitlines(True),
            fromfile="origin/source.txt", tofile="reproducer/" + repro_name))
        return "SOURCE_AND_DIFF", src, diff.encode("utf-8")
    if src is not None:
        raise ValueError("--origin-source only applies to origins ISSUE_VERBATIM_SNIPPET and AGENT_ADAPTED")
    return "NOT_APPLICABLE", None, None


def _evaluate(repo, python, claim_doc, repro_path, out_dir, runs=5, timeout=30, min_completed=3,
             gate=True, allow_unverified_provenance=False, origin="AGENT_ADAPTED", attempts=0,
             base_seed=1000, pythonpath_extra=None, sandbox=None, in_oracle=False, env_template=None,
             origin_source=None, checkout=None):
    """Evaluate one reproducer against one checkout. Returns the outcome dict (also written to out_dir)."""
    prov = provenance_state(claim_doc, allow_unverified_provenance)  # may raise ValueError
    claim_status, claim_note = claims.support(claim_doc["claim"])  # F-039: unknown kinds are UNSUPPORTED
    claim_kind = claims.kind(claim_doc["claim"])
    watch = claims.watch_target(claim_doc["claim"]) if claim_kind == claims.KIND_WRONG_OUTPUT else None
    with open(repro_path, "rb") as f:
        repro_bytes = f.read()
    repro_name = os.path.basename(repro_path)
    origin_evidence, origin_src, origin_diff = _origin_evidence(origin, origin_source, repro_bytes, repro_name)  # may raise
    os.makedirs(out_dir, exist_ok=True)
    if origin_src is not None:
        os.makedirs(os.path.join(out_dir, "origin"), exist_ok=True)
        with open(os.path.join(out_dir, "origin", "source.txt"), "wb") as f:
            f.write(origin_src)
        if origin_diff is not None:
            with open(os.path.join(out_dir, "origin", "adaptation.diff"), "wb") as f:
                f.write(origin_diff)
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

    template = _prepare_template(env_template, python, sandbox)
    env_info, env_sha = capture_environment(python, sandbox)
    sandbox_rec = sbx.record(sandbox)
    git = git_info(repo)
    tree_before, n_files = tree_hash(repo)
    write_json(os.path.join(out_dir, "environment.json"), {
        "interpreter": env_info, "environment_sha256": env_sha, "git": git,
        "repository_tree_sha256_before": tree_before, "repository_files_hashed": n_files,
        "environment_variables_allowed": env_names(), "sandbox": sandbox_rec,
        "environment_trust": "UNVERIFIED",
        "environment_isolation": ({"mode": ENV_FRESH, "template_tree_sha256": template["sha"],
                                   "template_files_hashed": template["files"]} if template
                                  else {"mode": ENV_SHARED}),
    })

    run_records = []
    if gate_res["status"] == C.GATE_VALID and claim_status == claims.READY and env_info["python"] is not None:
        for i in range(runs):
            run_dir = os.path.join(out_dir, "runs", "run-%02d" % (i + 1))
            run_python, copy_dir, copy_s = python, None, None
            if template:
                run_python, copy_dir, copy_s = _fresh_copy(template)
            try:
                raw = run_once(run_python, repo, repro_bytes, run_dir, timeout, base_seed + i * 7919,
                               pythonpath_extra, sandbox, watch)
            finally:
                if copy_dir:
                    shutil.rmtree(copy_dir, ignore_errors=True)
            after, _ = tree_hash(repo)
            rec = _run_record(i + 1, raw, claim_doc["claim"], tree_before, after)
            if copy_s is not None:
                rec["env_copy_seconds"] = copy_s
            write_json(os.path.join(run_dir, "run.json"), rec)
            run_records.append(rec)
    elif gate_res["status"] == C.GATE_VALID and claim_status == claims.READY:
        run_records = [{"index": i + 1, "seed": None, "status": C.RUN_ENV_FAILURE, "symptom_match": False,
                        "clean_completion": False, "reasons": ["INTERPRETER_LAUNCH_FAILED"],
                        "invalid_reason": None} for i in range(runs)]

    if checkout is not None:
        write_json(os.path.join(out_dir, "checkout.json"), checkout.finish())

    agg = aggregate(run_records, min_completed=min_completed, provenance=prov,
                    reproducer_status=gate_res["status"], claim_status=claim_status)
    anchors_verified, anchors_not_verified = _anchor_states(claim_doc)
    outcome = {
        "schema_version": SCHEMA_VERSION, "tool_version": __version__, "created_at": now_utc(),
        "outcome": agg["outcome"], "outcome_reason": agg["outcome_reason"],
        "outcome_qualifier": agg["outcome_qualifier"],
        "claim_status": claim_status, "reproducer_status": gate_res["status"],
        "claim_kind": claim_kind, "claim_kind_maturity": claims.MATURITY.get(claim_kind),
        "claim_support_note": claim_note,
        "run_status": [r["status"] for r in run_records], "counts": agg["counts"],
        "min_completed": min_completed, "runs_requested": runs,
        "reproducer_origin": origin, "attempts_before_submission": attempts,
        "claim_faithfulness": "NOT_REVIEWED", "observation_integrity": C.OBSERVATION_INTEGRITY,
        "environment_trust": "UNVERIFIED", "claim_provenance": prov, "sandbox": sandbox_rec,
        "repository": {"commit": git["commit"], "tree_sha256_before": tree_before},
        "environment_mode": ENV_FRESH if template else ENV_SHARED,
        "anchors_verified": anchors_verified, "anchors_not_verified": anchors_not_verified,
        "environment_sha256": env_sha, "reproducer_name": repro_name,
        "reproducer_sha256": gate_res["reproducer_sha256"], "claim_sha256": claim_doc.get("claim_sha256"),
        # F-015/F-020: a single run can be a false positive; only a passing before/after oracle is evidence
        "oracle_required": (not in_oracle) and agg["outcome"] in (C.SYMPTOM_REPRODUCED, C.SYMPTOM_REPRODUCED_FLAKY),
        "reproducer_origin_evidence": origin_evidence,
    }
    if origin_src is not None:
        outcome["reproducer_origin_source_sha256"] = sha256_bytes(origin_src)
    if origin_diff is not None:
        outcome["reproducer_origin_diff_sha256"] = sha256_bytes(origin_diff)
    write_json(os.path.join(out_dir, "outcome.json"), outcome)
    write_hashes(out_dir)
    return outcome


def evaluate(repo, python, claim_doc, repro_path, out_dir, checkout_sha=None, **kw):
    """checkout_sha (req_005): evaluate a fresh detached worktree of that full SHA made from repo (the source repository),
    removed afterwards; without it repo is used as given."""
    if checkout_sha is None:
        return _evaluate(repo, python, claim_doc, repro_path, out_dir, **kw)
    co = Checkout(repo, checkout_sha)
    try:
        return _evaluate(co.path, python, claim_doc, repro_path, out_dir, checkout=co, **kw)
    finally:
        co.finish()


def _is_int(x, minimum):
    return isinstance(x, int) and not isinstance(x, bool) and x >= minimum


def structure_problems(bundle, rec, env, claim):
    """F-036: the keys and files replay uses, checked before anything runs. Returns a list of problems."""
    p = []
    if not (isinstance(env, dict) and isinstance(env.get("git"), dict) and "commit" in env["git"]):
        p.append("environment.json has no git.commit")
    if not (isinstance(claim, dict) and isinstance(claim.get("claim"), dict)):
        p.append("claim.json has no claim object")
    name = rec.get("reproducer_name")
    # a plain file name only: joined to reproducer/, it must not leave the bundle (no hash covers files outside it)
    plain = (isinstance(name, str) and name not in ("", ".", "..") and not any(c in name for c in "/\\:")
             and os.path.basename(name) == name)
    if not plain:
        p.append("outcome.json reproducer_name is not a plain file name: %r" % (name,))
    elif not os.path.isfile(os.path.join(bundle, "reproducer", name)):
        p.append("missing reproducer/" + name)
    if not isinstance(rec.get("reproducer_origin"), str):
        p.append("outcome.json reproducer_origin is not a string")
    if not _is_int(rec.get("runs_requested"), 1):
        p.append("outcome.json runs_requested is not an integer >= 1")
    if not _is_int(rec.get("attempts_before_submission"), 0):
        p.append("outcome.json attempts_before_submission is not an integer >= 0")
    return p


def replay(bundle, repo, python, runs=None, timeout=30, sandbox=None, env_template=None):
    """Re-run a bundle's reproducer and compare with the recorded outcome. Never trusts bundle code blindly:
    the reproducer goes through the gate again and runs in fresh processes."""
    ok, problems = verify_hashes(bundle)
    report = {"hashes_ok": ok, "problems": problems, "replay_outcome": None, "same_outcome": None}
    if not ok:
        return report
    rec = read_json(os.path.join(bundle, "outcome.json"))
    # F-029: the recorded outcome must satisfy the cross-field invariants (hashes alone cannot catch an edited file
    # whose hashes.json was regenerated); an invalid recorded outcome is not replayed
    report["invariant_violations"] = validate_outcome(rec)
    report["invariants_ok"] = not report["invariant_violations"]
    if not report["invariants_ok"]:
        return report
    env = read_json(os.path.join(bundle, "environment.json"))
    claim = read_json(os.path.join(bundle, "claim.json"))
    report["structure_problems"] = structure_problems(bundle, rec, env, claim)
    if report["structure_problems"]:
        return report
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
                       origin=rec["reproducer_origin"], attempts=rec["attempts_before_submission"], sandbox=sandbox,
                       env_template=env_template,
                       origin_source=(os.path.join(bundle, "origin", "source.txt")
                                      if os.path.isfile(os.path.join(bundle, "origin", "source.txt")) else None))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    report["replay_outcome"] = [new["outcome"], new["outcome_reason"]]
    report["same_outcome"] = report["replay_outcome"] == report["recorded_outcome"]
    replay_violations = validate_outcome(new)
    if replay_violations:
        report["invariant_violations"] += ["REPLAY: " + x for x in replay_violations]
        report["invariants_ok"] = False
    return report


def oracle(before_repo, after_repo, python, claim_doc, repro_path, out_dir, after_python=None, before_sha=None,
           after_sha=None, **kw):
    """Before/after-fix oracle: the same reproducer must reproduce the symptom before the fix and
    complete CLEANLY after it ('no longer matches' is not enough: an ImportError is not a fix)."""
    before = evaluate(before_repo, python, claim_doc, repro_path, os.path.join(out_dir, "before"), in_oracle=True,
                      checkout_sha=before_sha, **kw)
    after = evaluate(after_repo, after_python or python, claim_doc, repro_path, os.path.join(out_dir, "after"), in_oracle=True,
                     checkout_sha=after_sha, **kw)
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
