"""Draw closed bug reports at random, so that the bugs are not chosen by the maintainer.

Protocol (fixed before the first draw, see labs/sample-2026-09/PROTOCOL.md):
  pool LIB: a random 14-day creation window between 2019-01-01 and 2025-06-30 (seeded RNG), GitHub search for
            closed issues labelled "bug" in Python repositories whose body contains a Python traceback; one result
            is picked at random from that window.
  pool APP: the repositories returned by the search  `topic:cli language:python stars:>3000`  (top 30 by stars) are
            the application list; the RNG picks one repository and one random closed "bug" issue with a traceback.
Mechanical eligibility (each draw is recorded, eligible or not, nothing is redrawn silently):
  E1 the last line of the traceback in the body names an exception type,
  E2 a fix commit is identifiable: the `closed` event references a commit, or a merged PR of the same repository
     cross-references the issue (its merge commit is the fix; the affected commit is the merge commit's first parent).
Usage: python tools/sample_issues.py --seed 20260929 --pool LIB --eligible 3 --out draws.json
Unauthenticated GitHub API (search 10/min, core 60/h). On a rate-limit answer the script waits for the reset time and
repeats the same call, so waiting never changes the sample. A token in the GITHUB_TOKEN environment variable, if set,
raises the limits; the script only reads it.

v3 additions (labs/sample-v3/PROTOCOL.md):
  pool NARROW: the RNG picks one package from --packages (labs/sample-v3/narrow-packages.json), then one closed issue of
               its repository whose body contains a Python traceback (no label filter).
  --exclude:   a JSON list of repositories; a draw on one of them is recorded as EXCLUDED_REPO and counts as a draw
               (NARROW checks the package's repository before searching; LIB/APP check the drawn issue's repository).
"""
import argparse
import datetime
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
TB = re.compile(r"^\s*((?:[A-Za-z_][\w.]*\.)?[A-Za-z_]\w*(?:Error|Exception|Exit|Interrupt))\b(?::\s*(.*))?$", re.M)


def get(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "reprogate-sampler"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    while True:
        try:
            with urllib.request.urlopen(urllib.request.Request(API + path, headers=headers), timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and e.headers.get("X-RateLimit-Remaining") == "0":
                wait = max(5, int(e.headers.get("X-RateLimit-Reset", "0")) - int(time.time()) + 5)
                print("rate limit, waiting %d s" % wait, file=sys.stderr)
                time.sleep(wait)
                continue
            raise


def last_exception(body):
    i = body.rfind("Traceback (most recent call last)")
    if i < 0:
        return None
    m = None
    for m in TB.finditer(body[i:]):
        pass
    return (m.group(1), (m.group(2) or "").strip()) if m else None


def find_fix(repo, number):
    """E2 (amended, see PROTOCOL.md): a `closed` event with a commit, else the merge commit of a merged PR in the
    same repository that cross-references the issue. Returns (sha, source) or None."""
    tl = get("/repos/%s/issues/%d/timeline?per_page=100" % (repo, number))
    for e in tl:
        if e.get("event") == "closed" and e.get("commit_id"):
            return e["commit_id"], "closed_event"
    for e in tl:
        src = (e.get("source") or {}).get("issue") or {}
        pr = src.get("pull_request") or {}
        if e.get("event") == "cross-referenced" and pr.get("merged_at") and src.get("repository_url", "").endswith("/" + repo):
            p = get("/repos/%s/pulls/%d" % (repo, src["number"]))
            if p.get("merged") and p.get("merge_commit_sha"):
                return p["merge_commit_sha"], "merged_pr#%d" % src["number"]
    return None


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


def pick_narrow(rng, packages, excluded):
    pkg = rng.choice(packages)
    repo = pkg["repo"]
    meta = {"package": pkg["project"], "rank": pkg["rank"], "repo": repo}
    if repo.lower() in excluded:
        return meta, "EXCLUDED", None
    q = 'repo:%s is:issue is:closed "Traceback (most recent call last)" in:body' % repo
    try:
        res = search(q)
    except urllib.error.HTTPError as e:  # 422: repository renamed, removed or not searchable
        meta["search_error"] = e.code
        return meta, None, None
    total = min(res.get("total_count", 0), 1000)
    meta["total"] = total
    if not total:
        return meta, None, None
    idx = rng.randrange(total)
    meta["index"] = idx
    items = res["items"] if idx < 100 else search(q, idx // 100 + 1)["items"]
    return meta, None, items[idx % 100] if idx % 100 < len(items) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--pool", choices=["LIB", "APP", "NARROW"], required=True)
    ap.add_argument("--packages", help="NARROW: the filtered package list")
    ap.add_argument("--exclude", help="JSON list of excluded repositories (v3)")
    ap.add_argument("--eligible", type=int, default=3)
    ap.add_argument("--max-draws", type=int, default=12)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rng = random.Random("%s/%s" % (a.seed, a.pool))
    repos = []
    if a.pool == "APP":
        res = get("/search/repositories?q=%s&sort=stars&per_page=30" % urllib.parse.quote("topic:cli language:python stars:>3000"))
        repos = [r["full_name"] for r in res["items"]]
    packages = json.load(open(a.packages, encoding="utf-8"))["packages"] if a.pool == "NARROW" else []
    excluded = {r.lower() for r in json.load(open(a.exclude, encoding="utf-8"))} if a.exclude else set()
    draws, ok = [], 0
    while ok < a.eligible and len(draws) < a.max_draws:
        flag = None
        if a.pool == "NARROW":
            meta, flag, it = pick_narrow(rng, packages, excluded)
        else:
            meta, it = pick_lib(rng) if a.pool == "LIB" else pick_app(rng, repos)
        rec = {"draw": len(draws) + 1, "pool": a.pool, "meta": meta}
        if flag == "EXCLUDED":
            rec["repo"] = meta["repo"]
            rec["verdict"] = "EXCLUDED_REPO"
        elif it is None:
            rec["verdict"] = "EMPTY_DRAW"
        else:
            repo = it["repository_url"].split("/repos/")[1]
            rec.update({"repo": repo, "number": it["number"], "title": it["title"], "url": it["html_url"]})
            exc = last_exception(it.get("body") or "")
            if repo.lower() in excluded:
                rec["verdict"] = "EXCLUDED_REPO"
            elif not exc:
                rec["verdict"] = "INELIGIBLE_E1_NO_EXCEPTION_LINE"
            else:
                rec["exception"] = {"type": exc[0], "message": exc[1]}
                fix = find_fix(repo, it["number"])
                if not fix:
                    rec["verdict"] = "INELIGIBLE_E2_NO_FIX_COMMIT"
                else:
                    rec["closing_commit"], rec["fix_source"] = fix
                    rec["verdict"] = "ELIGIBLE"
                    ok += 1
        draws.append(rec)
        print(rec["draw"], rec.get("repo"), rec.get("number"), rec["verdict"], file=sys.stderr)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"seed": a.seed, "pool": a.pool, "draws": draws}, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
