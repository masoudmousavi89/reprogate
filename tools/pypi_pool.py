"""Build the NARROW package pool of the v3 sample (labs/sample-v3/PROTOCOL.md): a snapshot of the most downloaded PyPI
packages and the filtered list the sampler draws from. Run once, before the draw; both outputs are committed.

    python tools/pypi_pool.py --top 1000 --snapshot labs/sample-v3/top-pypi-snapshot.json \
        --filtered labs/sample-v3/narrow-packages.json

Filter (fixed with the protocol):
  wheel  the latest release has a wheel whose tags include python tag `py3`, abi `none` and platform `any`
         (so `py2.py3-none-any` counts: it is a py3-none-any wheel);
  repo   the first github.com/<owner>/<repo> link, looking at the PyPI project URLs in this key order: source, source
         code, repository, code, github, then the remaining keys sorted by name, then the home page. Links whose
         owner is a GitHub feature path (sponsors, orgs, apps, marketplace, features, topics) are skipped.
Packages that fail a rule are listed with the reason, not dropped silently.
"""
import argparse
import datetime
import json
import re
import sys
import time
import urllib.error
import urllib.request

SOURCE = "https://hugovk.dev/top-pypi-packages/top-pypi-packages.min.json"
KEY_ORDER = ("source", "source code", "repository", "code", "github")
NOT_OWNERS = {"sponsors", "orgs", "apps", "marketplace", "features", "topics"}
GH = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", re.I)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "reprogate-sampler"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if attempt == 2:
                raise
        except urllib.error.URLError:
            if attempt == 2:
                raise
        time.sleep(3)
    return None


def py3_none_any(filename):
    """True for a wheel whose tag set contains py3-none-any."""
    if not filename.endswith(".whl"):
        return False
    parts = filename[:-4].split("-")
    if len(parts) < 5:
        return False
    py, abi, plat = parts[-3], parts[-2], parts[-1]
    return "py3" in py.split(".") and "none" in abi.split(".") and "any" in plat.split(".")


def github_repo(info):
    urls = info.get("project_urls") or {}
    lower = {k.lower(): v for k, v in urls.items() if isinstance(v, str)}
    ordered = [lower[k] for k in KEY_ORDER if k in lower]
    ordered += [lower[k] for k in sorted(lower) if k not in KEY_ORDER]
    if info.get("home_page"):
        ordered.append(info["home_page"])
    for u in ordered:
        for owner, repo in GH.findall(u):
            if owner.lower() in NOT_OWNERS:
                continue
            repo = re.sub(r"\.git$", "", repo)
            if repo and repo not in (".", ".."):
                return "%s/%s" % (owner, repo)
    return None


def classify(project, doc):
    if doc is None:
        return None, "NOT_ON_PYPI"
    wheels = [f["filename"] for f in doc.get("urls") or [] if py3_none_any(f.get("filename", ""))]
    if not wheels:
        return None, "NO_PY3_NONE_ANY_WHEEL"
    repo = github_repo(doc.get("info") or {})
    if not repo:
        return None, "NO_GITHUB_REPO"
    return {"project": project, "version": doc["info"]["version"], "wheel": wheels[0], "repo": repo}, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=1000)
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--filtered", required=True)
    a = ap.parse_args()
    data = fetch(SOURCE)
    rows = sorted(data["rows"], key=lambda r: -r["download_count"])[:a.top]
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    snap = {"source": SOURCE, "downloaded": today, "dataset_last_update": data.get("last_update"),
            "top": a.top, "rows": [{"rank": i + 1, "project": r["project"], "download_count": r["download_count"]}
                                   for i, r in enumerate(rows)]}
    kept, removed = [], []
    for r in snap["rows"]:
        entry, reason = classify(r["project"], fetch("https://pypi.org/pypi/%s/json" % r["project"]))
        if entry:
            entry["rank"] = r["rank"]
            kept.append(entry)
        else:
            removed.append({"rank": r["rank"], "project": r["project"], "reason": reason})
        if r["rank"] % 100 == 0:
            print(r["rank"], "kept", len(kept), file=sys.stderr)
    for path, doc in ((a.snapshot, snap),
                      (a.filtered, {"built": today, "from": a.snapshot, "rules": __doc__.split("Filter")[1].strip(),
                                    "kept": len(kept), "removed": len(removed), "packages": kept,
                                    "removed_packages": removed})):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=1)
            f.write("\n")
    print("kept %d of %d" % (len(kept), len(snap["rows"])), file=sys.stderr)


if __name__ == "__main__":
    main()
