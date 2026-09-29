"""Draw closed bug reports at random, so that the bugs are not chosen by the maintainer.

Protocol (fixed before the first draw, see labs/sample-2026-09/PROTOCOL.md):
  pool LIB: a random 14-day creation window between 2019-01-01 and 2025-06-30 (seeded RNG), GitHub search for
            closed issues labelled "bug" in Python repositories whose body contains a Python traceback; one result
            is picked at random from that window.
  pool APP: the repositories returned by the search  `topic:cli language:python stars:>3000`  (top 30 by stars) are
            the application list; the RNG picks one repository and one random closed "bug" issue with a traceback.
Mechanical eligibility (each draw is recorded, eligible or not, nothing is redrawn silently):
  E1 the last line of the traceback in the body names an exception type,
  E2 the issue's `closed` event references a commit (so an affected/fix commit pair exists).
Usage: python tools/sample_issues.py --seed 20260929 --pool LIB --eligible 3 --out draws.json
Unauthenticated GitHub API (search 10/min, core 60/h): calls are counted and the script stops on rate limit.
"""
import argparse
import datetime
import json
import random
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://api.github.com"
TB = re.compile(r"^\s*((?:[A-Za-z_][\w.]*\.)?[A-Za-z_]\w*(?:Error|Exception|Exit|Interrupt))\b(?::\s*(.*))?$", re.M)


def get(path):
    req = urllib.request.Request(API + path, headers={"Accept": "application/vnd.github+json", "User-Agent": "reprogate-sampler"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def last_exception(body):
    i = body.rfind("Traceback (most recent call last)")
    if i < 0:
        return None
    m = None
    for m in TB.finditer(body[i:]):
        pass
    return (m.group(1), (m.group(2) or "").strip()) if m else None


def search(q, page=1):
    time.sleep(7)
    return get("/search/issues?q=%s&per_page=100&page=%d" % (urllib.parse.quote(q), page))


def pick_lib(rng):
    d0, d1 = datetime.date(2019, 1, 1).toordinal(), datetime.date(2025, 6, 30).toordinal()
    a = datetime.date.fromordinal(rng.randint(d0, d1))
    b = a + datetime.timedelta(days=13)
    q = 'language:python is:issue is:closed label:bug "Traceback (most recent call last)" in:body created:%s..%s' % (a, b)
    res = search(q)
    items = res.get("items", [])
    return {"window": "%s..%s" % (a, b), "total": res.get("total_count", 0)}, (rng.choice(items) if items else None)


def pick_app(rng, repos):
    repo = rng.choice(repos)
    q = 'repo:%s is:issue is:closed label:bug "Traceback (most recent call last)" in:body' % repo
    res = search(q)
    total = min(res.get("total_count", 0), 1000)
    if not total:
        return {"repo": repo, "total": 0}, None
    idx = rng.randrange(total)
    items = res["items"] if idx < 100 else search(q, idx // 100 + 1)["items"]
    return {"repo": repo, "total": total, "index": idx}, items[idx % 100] if idx % 100 < len(items) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--pool", choices=["LIB", "APP"], required=True)
    ap.add_argument("--eligible", type=int, default=3)
    ap.add_argument("--max-draws", type=int, default=12)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rng = random.Random("%s/%s" % (a.seed, a.pool))
    repos = []
    if a.pool == "APP":
        res = get("/search/repositories?q=%s&sort=stars&per_page=30" % urllib.parse.quote("topic:cli language:python stars:>3000"))
        repos = [r["full_name"] for r in res["items"]]
    draws, ok = [], 0
    while ok < a.eligible and len(draws) < a.max_draws:
        meta, it = pick_lib(rng) if a.pool == "LIB" else pick_app(rng, repos)
        rec = {"draw": len(draws) + 1, "pool": a.pool, "meta": meta}
        if it is None:
            rec["verdict"] = "EMPTY_DRAW"
        else:
            repo = it["repository_url"].split("/repos/")[1]
            rec.update({"repo": repo, "number": it["number"], "title": it["title"], "url": it["html_url"]})
            exc = last_exception(it.get("body") or "")
            if not exc:
                rec["verdict"] = "INELIGIBLE_E1_NO_EXCEPTION_LINE"
            else:
                rec["exception"] = {"type": exc[0], "message": exc[1]}
                ev = get("/repos/%s/issues/%d/events" % (repo, it["number"]))
                cl = [e for e in ev if e.get("event") == "closed" and e.get("commit_id")]
                if not cl:
                    rec["verdict"] = "INELIGIBLE_E2_NO_CLOSING_COMMIT"
                else:
                    rec["closing_commit"] = cl[-1]["commit_id"]
                    rec["verdict"] = "ELIGIBLE"
                    ok += 1
        draws.append(rec)
        print(rec["draw"], rec.get("repo"), rec.get("number"), rec["verdict"], file=sys.stderr)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"seed": a.seed, "pool": a.pool, "draws": draws}, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
