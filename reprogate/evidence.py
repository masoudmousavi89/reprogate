"""Evidence bundle helpers: hashing and integrity check (hash = integrity only, not authenticity)."""
import os

from .util import read_json, sha256_file, write_json

HASHES = "hashes.json"


class BundleError(Exception):
    """The bundle cannot be read (F-035): not a folder, or a required JSON file is missing or not valid JSON."""

    def __init__(self, problems):
        Exception.__init__(self, "; ".join(problems))
        self.problems = problems


def load_bundle_json(bundle, names):
    """Read the JSON files a command needs, or raise BundleError naming every problem. Executes nothing."""
    if not os.path.isdir(bundle):
        raise BundleError(["evidence path is not a folder"])
    docs, problems = {}, []
    for name in names:
        p = os.path.join(bundle, name)
        if not os.path.isfile(p):
            problems.append("missing " + name)
            continue
        try:
            docs[name] = read_json(p)
        except ValueError:
            problems.append(name + " is not valid JSON")
        except OSError:
            problems.append(name + " cannot be read")
    if problems:
        raise BundleError(problems)
    return docs


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
