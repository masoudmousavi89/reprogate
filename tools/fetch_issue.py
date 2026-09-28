"""Download the RAW issue body from the GitHub API (stdlib only).

Writes <out>.api.json (exact API response) and <out>.body.md (exact bytes of the 'body' field).
Provenance spans/hashes must be computed on these bytes, never on rendered page text.
"""
import argparse
import json
import sys
import urllib.error
import urllib.request


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="pallets/jinja")
    ap.add_argument("--number", type=int, default=843)
    ap.add_argument("--out", required=True, help="output path prefix")
    a = ap.parse_args()
    url = "https://api.github.com/repos/%s/issues/%d" % (a.repo, a.number)
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": "reprogate-prototype"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
    except (urllib.error.URLError, OSError) as e:
        print("could not fetch %s: %s" % (url, e), file=sys.stderr)
        return 1
    data = json.loads(raw.decode("utf-8"))
    with open(a.out + ".api.json", "wb") as f:
        f.write(raw)
    with open(a.out + ".body.md", "wb") as f:
        f.write((data.get("body") or "").encode("utf-8"))
    print("wrote %s.api.json and %s.body.md (updated_at=%s, state=%s)" % (a.out, a.out, data.get("updated_at"), data.get("state")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
