"""Run f05_patch_target on Lab #1 (pre-fix commit via --checkout-sha): real gate, then gate bypassed. Windows/Linux host mode.
Usage (repo root): py -3.8 labs/adversarial-corpus/run_f05.py <jinja-clone> <python-of-pinned-venv> <out-dir>"""
import json
import os
import sys

sys.path.insert(0, os.getcwd())
from reprogate.pipeline import evaluate  # noqa: E402

SHA = "81825095d24f4dbccb40f787fff70db54989b91c"
src, python, out = sys.argv[1:4]
claim = json.load(open("labs/jinja-843/claim.frozen.json"))
repro = "labs/jinja-843/fixtures/f05_patch_target.py"
for name, gate in (("real_gate", True), ("gate_bypassed", False)):
    o = evaluate(src, python, claim, repro, os.path.join(out, name), checkout_sha=SHA, gate=gate, runs=5, timeout=30,
                 min_completed=3)
    print(name, "| gate:", o["reproducer_status"], "| outcome:", o["outcome"] + "/" + o["outcome_reason"],
          "| runs:", o["run_status"], "| counts:", o["counts"])
    g = json.load(open(os.path.join(out, name, "gate.json")))
    print("   gate findings:", [(f["code"], f["line"]) for f in g["findings"]])
