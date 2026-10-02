"""LEGACY / versioned bundle experiment on a REAL bundle (req_011). Usage (repo root):
py -3.8 labs/aggregation-rules/run_legacy_experiment.py <oracle/before bundle> <repo checkout> <python of the target venv>
Copies the bundle three times and edits the copies (never the original); prints what inspect and verify say."""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.getcwd())
from reprogate import cli  # noqa: E402
from reprogate.evidence import write_hashes  # noqa: E402
from reprogate.pipeline import replay  # noqa: E402

bundle, repo, python = sys.argv[1:4]
tmp = tempfile.mkdtemp(prefix="rg-agg-")


def variant(name, fn):
    d = os.path.join(tmp, name)
    shutil.copytree(bundle, d)
    p = os.path.join(d, "outcome.json")
    o = json.load(open(p))
    fn(o)
    json.dump(o, open(p, "w"), indent=2)
    write_hashes(d)
    return d


def old_shape(o):
    o["outcome"], o["outcome_reason"] = "SYMPTOM_REPRODUCED", "NONE"
    o["run_status"] = ["COMPLETED"] * 4 + ["TIMEOUT"]
    o["counts"].update({"total": 5, "completed": 4, "timeouts": 1, "matching": 4, "env_failures": 0, "invalid": 0,
                        "clean_completion_runs": 0})


def legacy(o):
    o.pop("aggregation_rules", None)
    old_shape(o)


rows = [("untouched real bundle", variant("untouched", lambda o: None)),
        ("LEGACY: field removed, old shape (4 matching + 1 TIMEOUT, SYMPTOM_REPRODUCED)", variant("legacy", legacy)),
        ("versioned 2, same old shape", variant("versioned_old_shape", old_shape)),
        ("aggregation_rules = 3", variant("unknown", lambda o: o.update({"aggregation_rules": "3"})))]
for title, d in rows:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli.main(["inspect", "--evidence", d])
    lines = [l for l in buf.getvalue().splitlines() if l.startswith(("aggregation", "invariants"))]
    rep = replay(d, repo, python)
    print("== " + title)
    print("   inspect exit %d | %s" % (code, " | ".join(l.strip()[:150] for l in lines)))
    print("   verify: invariants_ok=%s same_outcome=%s aggregation_rules=%s legacy_timeout_semantics=%s" % (
        rep.get("invariants_ok"), rep.get("same_outcome"), rep.get("aggregation_rules"), rep.get("legacy_timeout_semantics")))
shutil.rmtree(tmp, ignore_errors=True)
