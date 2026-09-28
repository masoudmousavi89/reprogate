"""Compare Lab #1 results with the expected outcomes that were written BEFORE the real run."""
import argparse
import json
import os
import sys


def load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--expected", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    exp = load(a.expected)
    rows = []
    for case, want in exp.items():
        if case.startswith("_"):
            continue
        d = os.path.join(a.evidence, case)
        if case == "oracle":
            p = os.path.join(d, "oracle.json")
            if not os.path.exists(p):
                rows.append((case, str(want), "MISSING", False))
                continue
            got = load(p)
            actual = {"before_outcome": got["before_outcome"], "post_fix_classification": got["post_fix_classification"],
                      "oracle_pass": got["oracle_pass"]}
            ok = all(actual[k] == want[k] for k in want)
            rows.append((case, "before=%s post=%s pass=%s" % (want["before_outcome"], want["post_fix_classification"], want["oracle_pass"]),
                         "before=%s post=%s pass=%s" % (actual["before_outcome"], actual["post_fix_classification"], actual["oracle_pass"]), ok))
            continue
        p = os.path.join(d, "outcome.json")
        if not os.path.exists(p):
            rows.append((case, "%s/%s" % (want["outcome"], want["reason"]), "MISSING", False))
            continue
        got = load(p)
        actual = "%s/%s" % (got["outcome"], got["outcome_reason"])
        wanted = "%s/%s" % (want["outcome"], want["reason"])
        rows.append((case, wanted, actual, actual == wanted))
    lines = ["| case | expected | actual | ok |", "|---|---|---|---|"]
    for c, w, g, ok in rows:
        lines.append("| %s | %s | %s | %s |" % (c, w, g, "YES" if ok else "NO"))
    text = "\n".join(lines) + "\n"
    print(text)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
    return 0 if all(r[3] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
