import argparse
import json
import os
import sys

from . import __version__
from .evidence import verify_hashes
from .gate import gate_source
from .pipeline import evaluate, oracle, replay
from .provenance import check_claim
from .util import read_json, write_json

HOST_WARNING = (
    "WARNING: prototype host mode. The reproducer runs as a normal process on THIS computer "
    "(no sandbox, no network isolation). Only run reproducers you have read and trust.\n"
    "Pass --allow-host-execution to confirm."
)


def _need_host_flag(a):
    if not a.allow_host_execution:
        print(HOST_WARNING, file=sys.stderr)
        return False
    return True


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


def _kw(a):
    return dict(runs=a.runs, timeout=a.timeout, min_completed=a.min_completed,
                allow_unverified_provenance=a.allow_unverified_provenance, origin=a.origin,
                attempts=a.attempts, pythonpath_extra=a.pythonpath_extra)


def cmd_claim_check(a):
    doc = _load_claim(a.claim)
    with open(a.issue_body, "rb") as f:
        body = f.read()
    frozen = check_claim(doc, body)
    write_json(a.out, frozen)
    for x in frozen["anchors"]:
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
        out = evaluate(a.repo, a.python, _load_claim(a.claim), a.reproducer, a.out, **_kw(a))
    except ValueError as e:
        print("ERROR:", e, file=sys.stderr)
        return 2
    print("outcome:", out["outcome"], "| reason:", out["outcome_reason"],
          "| qualifier:", out["outcome_qualifier"])
    print("runs:", out["run_status"], "| counts:", out["counts"])
    print("evidence:", a.out)
    return 0


def cmd_oracle(a):
    if not _need_host_flag(a):
        return 2
    try:
        res = oracle(a.before_repo, a.after_repo, a.python, _load_claim(a.claim), a.reproducer, a.out,
                     after_python=a.after_python, **_kw(a))
    except ValueError as e:
        print("ERROR:", e, file=sys.stderr)
        return 2
    print("before:", res["before_outcome"], "| after:", res["after_outcome"],
          "| post-fix:", res["post_fix_classification"])
    print("ORACLE", "PASS" if res["oracle_pass"] else "FAIL")
    return 0 if res["oracle_pass"] else 1


def cmd_verify(a):
    if not _need_host_flag(a):
        return 2
    rep = replay(a.evidence, a.repo, a.python, timeout=a.timeout)
    print(json.dumps(rep, indent=2))
    ok = rep["hashes_ok"] and rep.get("same_outcome") and rep.get("commit_matches") is not False
    print("VERIFY", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def cmd_inspect(a):
    ok, problems = verify_hashes(a.evidence)
    o = read_json(os.path.join(a.evidence, "outcome.json"))
    print("outcome            :", o["outcome"], "(%s)" % o["outcome_reason"])
    print("qualifier          :", o["outcome_qualifier"])
    print("reproducer         :", o["reproducer_name"], o["reproducer_origin"], o["reproducer_status"])
    print("runs               :", o["run_status"])
    print("counts             :", o["counts"])
    print("claim provenance   :", o["claim_provenance"])
    print("observation        :", o["observation_integrity"], "| environment trust:", o["environment_trust"])
    print("sandbox            :", o["sandbox"]["kind"])
    print("hashes             :", "OK" if ok else "PROBLEMS: %s" % problems)
    return 0


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
    p.add_argument("--python", required=True, help="target interpreter (e.g. the venv python)")
    p.add_argument("--out", required=True)
    _common_run_args(p)
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("oracle", help="before/after-fix oracle")
    p.add_argument("--before-repo", required=True)
    p.add_argument("--after-repo", required=True)
    p.add_argument("--python", required=True)
    p.add_argument("--after-python")
    p.add_argument("--out", required=True)
    _common_run_args(p)
    p.set_defaults(fn=cmd_oracle)

    p = sub.add_parser("verify", help="replay an evidence bundle")
    p.add_argument("--evidence", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--python", required=True)
    p.add_argument("--timeout", type=float, default=30.0)
    p.add_argument("--allow-host-execution", action="store_true")
    p.set_defaults(fn=cmd_verify)

    p = sub.add_parser("inspect", help="print a human-readable summary of a bundle")
    p.add_argument("--evidence", required=True)
    p.set_defaults(fn=cmd_inspect)

    a = ap.parse_args(argv)
    return a.fn(a)
