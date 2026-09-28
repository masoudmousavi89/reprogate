"""Evidence bundle helpers: hashing and integrity check (hash = integrity only, not authenticity)."""
import os

from .util import read_json, sha256_file, write_json

HASHES = "hashes.json"


def build_hashes(bundle):
    out = {}
    for dirpath, _dirs, files in os.walk(bundle):
        for name in sorted(files):
            p = os.path.join(dirpath, name)
            rel = os.path.relpath(p, bundle).replace(os.sep, "/")
            if rel == HASHES or rel.startswith("runs/") and "/work/" in rel:
                continue
            out[rel] = sha256_file(p)
    return dict(sorted(out.items()))


def write_hashes(bundle):
    write_json(os.path.join(bundle, HASHES), {"algorithm": "sha256", "files": build_hashes(bundle)})


def verify_hashes(bundle):
    problems = []
    p = os.path.join(bundle, HASHES)
    if not os.path.exists(p):
        return False, ["hashes.json missing"]
    recorded = read_json(p).get("files", {})
    current = build_hashes(bundle)
    for rel, h in recorded.items():
        if rel not in current:
            problems.append("missing file: " + rel)
        elif current[rel] != h:
            problems.append("hash mismatch: " + rel)
    for rel in current:
        if rel not in recorded:
            problems.append("unrecorded file: " + rel)
    return not problems, problems
