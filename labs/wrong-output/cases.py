"""wrong_output version 1 cases (DESIGN.md). Synthetic library, host mode, sys.executable; only our own scripts run.

Usage (repo root): py -3.8 labs/wrong-output/cases.py
Part A runs reproducers through the real pipeline (evaluate / oracle) against a synthetic library with a known bug.
Part B calls the matcher directly with hand-made observations (forged frame, forged-by-protocol return).
Prints one line per case: id | outcome/reason (before) | oracle pass (where relevant) | claim_kind_maturity.
"""
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from reprogate.matcher import classify_run  # noqa: E402
from reprogate.pipeline import evaluate, oracle  # noqa: E402

LIB = '''
def change(paid, price):
    if price > paid:
        raise ValueError("not enough money")
    return paid - price%s


def buy(paid, price):
    return {"change": change(paid, price)}
'''
def make_repo(root, fixed):
    pkg = os.path.join(root, "shoplib")
    os.makedirs(pkg)
    with open(os.path.join(pkg, "money.py"), "w") as f:
        f.write(LIB % ("" if fixed else " - 100"))
    with open(os.path.join(pkg, "__init__.py"), "w") as f:
        f.write("from .money import change, buy\n")
    return root


def claim(expected="300", actual="200", kind="wrong_output"):
    c = {"kind": kind, "target": {"file": "shoplib/money.py", "function": "change"},
         "input": "change(1000, 700)", "expected": expected, "actual": actual}
    return {"schema_version": "0.1-proto", "issue": {"number": 1}, "claim": c, "anchors": []}


REPROS = {
    "w01_correct": "from shoplib import change\nprint(change(1000, 700))\n",
    "w02_print_only": "import shoplib\nprint(200)\n",
    "w03_own_function": "import shoplib\n\ndef change(paid, price):\n    return paid - price - 100\n\nprint(change(1000, 700))\n",
    "w04_replace_target": "import shoplib.money\nshoplib.money.change = lambda paid, price: 200\nprint(shoplib.money.change(1000, 700))\n",
    "w05_other_input": "from shoplib import change\nprint(change(900, 700))\n",
    "w06_exception": "from shoplib import change\nprint(change(500, 700))\n",
    "w07_indirect": "from shoplib import buy\nprint(buy(1000, 700))\n",
    "w10_non_literal_expected": "from shoplib import change\nprint(change(1000, 700))\n",
    "w11_unsupported_kind": "from shoplib import change\nprint(change(1000, 700))\n",
}
ORACLE_CASES = ("w01_correct", "w07_indirect")
FAST = dict(runs=3, timeout=30, min_completed=3, allow_unverified_provenance=True)


def part_a():
    tmp = tempfile.mkdtemp(prefix="rg-wo-")
    try:
        before = make_repo(os.path.join(tmp, "before"), fixed=False)
        after = make_repo(os.path.join(tmp, "after"), fixed=True)
        for cid, src in REPROS.items():
            doc = claim()
            if cid == "w10_non_literal_expected":
                doc = claim(expected="a Change object worth 300")
            if cid == "w11_unsupported_kind":
                doc = claim(kind="unexpected_exit")
            repro = os.path.join(tmp, cid + ".py")
            with open(repro, "w") as f:
                f.write(src)
            try:
                if cid in ORACLE_CASES:
                    res = oracle(before, after, sys.executable, doc, repro, os.path.join(tmp, "ev-" + cid), **FAST)
                    line = "%s | oracle %s" % (res["before_outcome"], "PASS" if res["oracle_pass"] else "FAIL")
                else:
                    o = evaluate(before, sys.executable, doc, repro, os.path.join(tmp, "ev-" + cid), **FAST)
                    line = "%s/%s | kind maturity %s" % (o["outcome"], o["outcome_reason"], o.get("claim_kind_maturity"))
            except Exception as e:  # recorded as observed
                line = "CRASH %s: %s" % (type(e).__name__, str(e)[:80])
            print("%-26s | %s" % (cid, line))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def frame(cls, rel="shoplib/money.py", function="change", authentic=True):
    return {"index": 1, "class": cls, "function": function, "rel_path": rel, "authentic": authentic}


def part_b():
    c = claim()["claim"]
    forged = {"exit_code": 0, "phase": "trigger", "exception": None,
              "returns": [{"frame": frame("FORGED_TARGET", authentic=False), "value_repr": "200", "args_repr": "(1000, 700)"}]}
    protocol = {"exit_code": 0, "phase": "trigger", "exception": None,
                "returns": [{"frame": frame("TARGET"), "value_repr": "200", "args_repr": "(1000, 700)"}]}
    for cid, obs in (("w08_forged_frame", forged), ("w09_protocol_forgery", protocol)):
        try:
            v = classify_run(obs, c)
            line = "match %s | reasons %s" % (v["symptom_match"], ",".join(v["reasons"]))
        except Exception as e:
            line = "CRASH %s: %s" % (type(e).__name__, str(e)[:80])
        print("%-26s | %s" % (cid, line))


if __name__ == "__main__":
    part_a()
    part_b()
