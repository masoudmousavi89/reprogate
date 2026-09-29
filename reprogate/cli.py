import argparse
import json
import sys

from . import __version__
from .evidence import BundleError, load_bundle_json, verify_hashes
from .gate import gate_source
from .invariants import validate_outcome
from .pipeline import evaluate, oracle, replay
from . import sandbox as sbx
from .provenance import check_claim
from .util import read_json, write_json

HOST_WARNING = (
    "WARNING: prototype host mode. The reproducer runs as a normal process on THIS computer "
    "(no sandbox, no network isolation). Only run reproducers you have read and trust.\n"
    "Pass --allow-host-execution to confirm."
)


def _sandbox(a):
    if getattr(a, "sandbox", "none") != "docker":
        return None
    if not a.image:
        raise ValueError("--sandbox docker needs --image")
    return sbx.make(a.image)


def _python(a):
    if _sandbox(a) is not None:
        return "python"
    if not a.python:
        raise ValueError("--python is required unless --sandbox docker is used")
    return a.python


def _need_host_flag(a):
    if getattr(a, "sandbox", "none") == "docker":
        return True
    if not a.allow_host_execution:
        print(HOST_WARNING, file=sys.stderr)
        return False
    return True


def _invalid_bundle(e):
    # F-035: exit 2 = incomplete input; exit 1 stays for a readable bundle that is invalid or fails
    print("INVALID_BUNDLE:", "; ".join(e.problems), file=sys.stderr)
    return 2


def _load_claim(path):
    doc = read_json(path)
    if "claim" not in doc:
        raise ValueError("claim file has no 'claim' object")
    return doc


def _common_run_args(p):
    p.add_argument("--claim", required=True)
    p.add_argument("--reproducer", required=True)
    p.add_argument("--runs", type=int, default=5)
    p.add_argument("--timeout", type=float, default=30.0)
    p.add_argument("--min-completed", type=int, default=3)
    p.add_argument("--allow-host-execution", action="store_true")
    p.add_argument("--allow-unverified-provenance", action="store_true")
    p.add_argument("--origin", default="AGENT_ADAPTED",
                   choices=["ISSUE_VERBATIM_SNIPPET", "AGENT_ADAPTED", "AGENT_AUTHORED", "HUMAN_AUTHORED"])
    p.add_argument("--attempts", type=int, default=0)
    p.add_argument("--pythonpath-extra", action="append", default=[])
    _env_template_arg(p)
    _sandbox_args(p)


def _env_template_arg(p):
    p.add_argument("--env-template", help="host mode: copy this environment directory afresh for every run "
                                          "(--python must be inside it); aborts if the template changes")


def _sandbox_args(p):
    p.add_argument("--sandbox", choices=["none", "docker"], default="none",
                   help="docker: run the reproducer in a network-less, read-only container (needs --image)")
    p.add_argument("--image", help="docker image holding the target Python and the target's dependencies")


def _kw(a):
    return dict(runs=a.runs, timeout=a.timeout, min_completed=a.min_completed,
                allow_unverified_provenance=a.allow_unverified_provenance, origin=a.origin,
                attempts=a.attempts, pythonpath_extra=a.pythonpath_extra, sandbox=_sandbox(a),
                env_template=a.env_template)


def cmd_claim_check(a):
    doc = _load_claim(a.claim)
    with open(a.issue_body, "rb") as f:
        body = f.read()
    frozen = check_claim(doc, body)
    write_json(a.out, frozen)
    for x in frozen["anchors"]:
        if x.get("reject_reason"):
            span = "%s (occurrences=%s)" % (x["reject_reason"], x.get("occurrences", 0))
        else:
            span = "%s-%s" % (x.get("start_byte"), x.get("end_byte")) if x["found"] else "NOT FOUND"
        print("%-20s %-12s %s" % (x["field"], x["provenance"], span))
    print("provenance_sufficient:", frozen["provenance_sufficient"])
    print("wrote", a.out)
    return 0 if frozen["provenance_sufficient"] else 1


def cmd_gate(a):
    with open(a.reproducer, "rb") as f:
        res = gate_source(f.read())
    print(json.dumps(res, indent=2))
    return 0 if res["status"] == "VALID" else 1


def cmd_run(a):
    if not _need_host_flag(a):
        return 2
    try:
        out = evaluate(a.repo, _python(a), _load_claim(a.claim), a.reproducer, a.out, **_kw(a))
    except ValueError as e:
        print("ERROR:", e, file=sys.stderr)
        return 2
    print("outcome:", out["outcome"], "| reason:", out["outcome_reason"],
          "| qualifier:", out["outcome_qualifier"])
    print("runs:", out["run_status"], "| counts:", out["counts"])
    if out.get("oracle_required"):
        print("oracle_required: yes (a single run can be a false positive; run `oracle` before reading this as evidence)")
    print("evidence:", a.out)
    return 0


def cmd_oracle(a):
    if not _need_host_flag(a):
        return 2
    try:
        res = oracle(a.before_repo, a.after_repo, _python(a), _load_claim(a.claim), a.reproducer, a.out,
                     after_python=a.after_python, **_kw(a))
    except ValueError as e:
        print("ERROR:", e, file=sys.stderr)
        return 2
    print("before:", res["before_outcome"], "| after:", res["after_outcome"],
          "| post-fix:", res["post_fix_classification"])
    print("ORACLE", "PASS" if res["oracle_pass"] else "FAIL")
    return 0 if res["oracle_pass"] else 1


def cmd_verify(a):
    try:
        load_bundle_json(a.evidence, ["outcome.json", "environment.json", "claim.json"])
    except BundleError as e:
        print("VERIFY FAIL (INVALID_BUNDLE)")
        return _invalid_bundle(e)
    if not _need_host_flag(a):
        return 2
    try:
        rep = replay(a.evidence, a.repo, _python(a), timeout=a.timeout, sandbox=_sandbox(a),
                     env_template=a.env_template)
    except ValueError as e:
        print("ERROR:", e, file=sys.stderr)
        return 2
    print(json.dumps(rep, indent=2))
    ok = (rep["hashes_ok"] and rep.get("invariants_ok") and rep.get("same_outcome")
          and rep.get("commit_matches") is not False)
    for x in rep.get("invariant_violations") or []:
        print("INVARIANT VIOLATION:", x, file=sys.stderr)
    print("VERIFY", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def cmd_inspect(a):
    try:
        o = load_bundle_json(a.evidence, ["outcome.json"])["outcome.json"]
    except BundleError as e:
        return _invalid_bundle(e)
    ok, problems = verify_hashes(a.evidence)
    # print what is there; a field the validator does not require may be absent (shown as "-")
    g = (lambda k: o.get(k, "-")) if isinstance(o, dict) else (lambda k: "-")
    sandbox = g("sandbox")
    print("outcome            :", g("outcome"), "(%s)" % g("outcome_reason"))
    print("qualifier          :", g("outcome_qualifier"))
    print("reproducer         :", g("reproducer_name"), g("reproducer_origin"), g("reproducer_status"))
    print("runs               :", g("run_status"))
    print("counts             :", g("counts"))
    print("claim provenance   :", g("claim_provenance"))
    print("observation        :", g("observation_integrity"), "| environment trust:", g("environment_trust"))
    print("oracle required    :", o.get("oracle_required") if isinstance(o, dict) else None)
    print("sandbox            :", sandbox.get("kind", "-") if isinstance(sandbox, dict) else sandbox)
    print("hashes             :", "OK" if ok else "PROBLEMS: %s" % problems)
    violations = validate_outcome(o)
    print("invariants         :", "OK" if not violations else "VIOLATIONS: %s" % violations)
    return 0 if not violations else 1


def main(argv=None):
    ap = argparse.ArgumentParser(prog="reprogate", description="ReproGate prototype %s" % __version__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("claim-check", help="verify claim anchors against the raw issue body")
    p.add_argument("--claim", required=True)
    p.add_argument("--issue-body", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_claim_check)

    p = sub.add_parser("gate", help="run the static reproducer gate only (never executes the file)")
    p.add_argument("--reproducer", required=True)
    p.set_defaults(fn=cmd_gate)

    p = sub.add_parser("run", help="evaluate one reproducer on one checkout")
    p.add_argument("--repo", required=True)
    p.add_argument("--python", help="target interpreter (e.g. the venv python); not needed with --sandbox docker")
    p.add_argument("--out", required=True)
    _common_run_args(p)
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("oracle", help="before/after-fix oracle")
    p.add_argument("--before-repo", required=True)
    p.add_argument("--after-repo", required=True)
    p.add_argument("--python")
    p.add_argument("--after-python")
    p.add_argument("--out", required=True)
    _common_run_args(p)
    p.set_defaults(fn=cmd_oracle)

    p = sub.add_parser("verify", help="replay an evidence bundle")
    p.add_argument("--evidence", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--python")
    p.add_argument("--timeout", type=float, default=30.0)
    p.add_argument("--allow-host-execution", action="store_true")
    _env_template_arg(p)
    _sandbox_args(p)
    p.set_defaults(fn=cmd_verify)

    p = sub.add_parser("inspect", help="print a human-readable summary of a bundle")
    p.add_argument("--evidence", required=True)
    p.set_defaults(fn=cmd_inspect)

    a = ap.parse_args(argv)
    return a.fn(a)
