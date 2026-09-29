"""Hash problems in inspect and structure of a readable bundle in verify (F-036). No reproducer is executed.

Usage (repo root): py -3.8 labs/bundle-structure/cases.py
Builds synthetic bundles with the helpers of labs/incomplete-bundle/cases.py and calls the CLI in-process. Every verify
case stops before a reproducer could run (missing or escaping reproducer file, bad JSON, missing key, hash problem).
Prints one line per case: id | command | exit code or CRASH <exception type> | INVALID_BUNDLE if stderr carries it.
"""
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from reprogate.evidence import write_hashes  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "incomplete_bundle_cases", os.path.join(ROOT, "labs", "incomplete-bundle", "cases.py"))
IB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(IB)
full, write, run_case, valid_outcome = IB.full, IB.write, IB.run_case, IB.valid_outcome


def edit_after_hashing(d):
    full(d)
    IB.write(os.path.join(d, "gate.json"), {"status": "VALID", "edited": True})
    return d


def add_after_hashing(d):
    full(d)
    with open(os.path.join(d, "extra.txt"), "w") as f:
        f.write("added later\n")
    return d


def remove_recorded(d):
    full(d)
    os.remove(os.path.join(d, "gate.json"))
    return d


def no_hashes(d):
    return full(d, hashes=False)


def hashes_text(text):
    def build(d):
        full(d)
        with open(os.path.join(d, "hashes.json"), "w", encoding="utf-8") as f:
            f.write(text)
        return d
    return build


def rehashed(mutate):
    def build(d):
        full(d)
        mutate(d)
        write_hashes(d)
        return d
    return build


def _env_without_git(d):
    write(os.path.join(d, "environment.json"), {"environment_sha256": "0" * 64})


def _outcome_with(**changes):
    def mutate(d):
        o = valid_outcome()
        for k, v in changes.items():
            if v is None:
                o.pop(k, None)
            else:
                o[k] = v
        write(os.path.join(d, "outcome.json"), o)
    return mutate


def _repro_removed(d):
    os.remove(os.path.join(d, "reproducer", "r.py"))


def _claim_is_list(d):
    write(os.path.join(d, "claim.json"), [1])


VERIFY = ["--repo", ROOT, "--python", sys.executable, "--allow-host-execution"]
CASES = [
    ("h01_hash_mismatch", "inspect", edit_after_hashing, []),
    ("h02_unrecorded_file", "inspect", add_after_hashing, []),
    ("h03_recorded_file_removed", "inspect", remove_recorded, []),
    ("h04_hashes_missing", "inspect", no_hashes, []),
    ("h05_hashes_missing", "verify", no_hashes, VERIFY),
    ("h06_hashes_not_json", "inspect", hashes_text('{"files": '), []),
    ("h07_hashes_not_json", "verify", hashes_text('{"files": '), VERIFY),
    ("h08_hashes_is_a_list", "inspect", hashes_text(json.dumps([1])), []),
    ("h09_hashes_is_a_list", "verify", hashes_text(json.dumps([1])), VERIFY),
    ("h10_environment_without_git", "verify", rehashed(_env_without_git), VERIFY),
    ("h11_outcome_without_reproducer_name", "verify", rehashed(_outcome_with(reproducer_name=None)), VERIFY),
    ("h12_reproducer_file_removed", "verify", rehashed(_repro_removed), VERIFY),
    ("h13_reproducer_name_escapes", "verify", rehashed(_outcome_with(reproducer_name="../missing.py")), VERIFY),
    ("h14_claim_is_a_list", "verify", rehashed(_claim_is_list), VERIFY),
    ("h15_outcome_without_runs_requested", "verify", rehashed(_outcome_with(runs_requested=None)), VERIFY),
]


if __name__ == "__main__":
    for c in CASES:
        print(run_case(*c))
