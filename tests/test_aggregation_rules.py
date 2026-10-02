"""Versioned aggregation rules (req_011, labs/aggregation-rules/PREDICTIONS.md): LEGACY bundles, the TIMEOUT_RULE invariant, inspect and verify."""
import contextlib
import copy
import io
import json
import os
import unittest

from reprogate import cli
from reprogate import constants as C
from reprogate.evidence import write_hashes
from reprogate.invariants import validate_outcome
from reprogate.outcome import aggregate
from reprogate.pipeline import evaluate, replay
from tests import helpers as H
from tests.test_outcome import run

FAST = dict(runs=5, timeout=20, min_completed=3)


def record(runs, **extra):
    r = aggregate(runs)
    o = {"outcome": r["outcome"], "outcome_reason": r["outcome_reason"], "outcome_qualifier": None,
         "claim_status": "READY", "reproducer_status": C.GATE_VALID, "claim_provenance": "VERIFIED",
         "run_status": [x["status"] for x in runs], "counts": r["counts"], "min_completed": 3,
         "runs_requested": len(runs), "oracle_required": False}
    o.update(extra)
    return o


def legacy_shape(o):
    """The old-semantics shape: 4 matching runs and 1 TIMEOUT, still SYMPTOM_REPRODUCED."""
    o = copy.deepcopy(o)
    o["outcome"], o["outcome_reason"] = C.SYMPTOM_REPRODUCED, C.NONE
    o["run_status"] = [C.RUN_COMPLETED] * 4 + [C.RUN_TIMEOUT]
    o["counts"].update({"total": 5, "completed": 4, "timeouts": 1, "matching": 4, "env_failures": 0, "invalid": 0,
                        "clean_completion_runs": 0})
    return o


class InvariantTests(unittest.TestCase):
    base = staticmethod(lambda: record([run(match=True)] * 5))

    def test_new_outcomes_are_versioned_and_valid(self):
        o = self.base()
        o["aggregation_rules"] = "2"
        self.assertEqual(validate_outcome(o), [])

    def test_timeout_rule_applies_only_to_versioned_bundles(self):
        shaped = legacy_shape(self.base())
        self.assertEqual(validate_outcome(shaped), [])  # LEGACY: no field, never subject to it (the stated loophole)
        shaped["aggregation_rules"] = "2"
        v = validate_outcome(shaped)
        self.assertTrue(any(x.startswith("TIMEOUT_RULE") for x in v), v)

    def test_unknown_versions_are_refused(self):
        for bad in ("3", 1, 2, "", None, ["2"]):
            o = self.base()
            o["aggregation_rules"] = bad
            v = validate_outcome(o)
            self.assertTrue(any(x.startswith("ENUM") for x in v), (bad, v))

    def test_dominating_reasons_and_other_shapes_stay_valid_when_versioned(self):
        T = run(C.RUN_TIMEOUT)
        mod = run(C.RUN_INVALID, invalid=C.REPOSITORY_MODIFIED)
        harness = run(C.RUN_INVALID, invalid="HARNESS_ERROR")
        for runs in ([T, mod] + [run(match=True)] * 3, [T, harness] + [run(match=True)] * 3, [T] * 5,
                     [T] + [run(match=True)] * 4, [run(C.RUN_ENV_FAILURE)] * 5):
            o = record(runs, aggregation_rules="2")
            self.assertEqual(validate_outcome(o), [], (o["outcome"], o["outcome_reason"]))

    def test_gate_rejected_and_claim_unsupported_versioned(self):
        o = record([], aggregation_rules="2")
        o.update({"outcome": C.NOT_EVALUATED, "outcome_reason": C.REPRODUCER_REJECTED,
                  "reproducer_status": C.GATE_REJECTED, "runs_requested": 5})
        self.assertEqual(validate_outcome(o), [])
        o = record([], aggregation_rules="2")
        o.update({"outcome": C.NOT_EVALUATED, "outcome_reason": C.CLAIM_UNSUPPORTED, "claim_status": "UNSUPPORTED",
                  "runs_requested": 5})
        self.assertEqual(validate_outcome(o), [])


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = H.tmpdir()
        self.addCleanup(H.cleanup, self.tmp)
        self.buggy = H.make_repo(os.path.join(self.tmp, "buggy"))
        self.claim = H.verified_claim()
        repro = H.write_repro(self.tmp, "good.py", H.GOOD_REPRO)
        self.out = os.path.join(self.tmp, "ev")
        self.o = evaluate(self.buggy, H.PYTHON, self.claim, repro, self.out, **FAST)

    def edit(self, fn):
        p = os.path.join(self.out, "outcome.json")
        with open(p) as f:
            o = json.load(f)
        fn(o)
        with open(p, "w") as f:
            json.dump(o, f, indent=2)
        write_hashes(self.out)

    def inspect(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli.main(["inspect", "--evidence", self.out])
        return code, buf.getvalue()

    def test_a_real_bundle_is_versioned_and_inspect_says_so(self):
        self.assertEqual(self.o["aggregation_rules"], "2")
        code, text = self.inspect()
        self.assertEqual(code, 0)
        self.assertIn("aggregation rules  : 2", text)
        self.assertNotIn("LEGACY", text)

    def test_every_outcome_kind_carries_the_field(self):
        rejected = H.write_repro(self.tmp, "bad.py", "from minilib import Box\nraise IndexError('pop from an empty deque')\n")
        o = evaluate(self.buggy, H.PYTHON, self.claim, rejected, os.path.join(self.tmp, "ev2"), **FAST)
        self.assertEqual((o["outcome"], o["aggregation_rules"]), (C.NOT_EVALUATED, "2"))

    def test_legacy_bundle_old_shape_inspects_ok_and_verifies(self):
        def to_legacy(o):
            del o["aggregation_rules"]
            o.update(legacy_shape(o))
        self.edit(to_legacy)
        code, text = self.inspect()
        self.assertEqual(code, 0, text)
        self.assertIn("LEGACY", text)
        rep = replay(self.out, self.buggy, H.PYTHON)
        self.assertTrue(rep["invariants_ok"] and rep["same_outcome"], rep)
        self.assertEqual(rep["aggregation_rules"], "LEGACY")
        self.assertTrue(rep["legacy_timeout_semantics"])

    def test_versioned_bundle_with_the_old_shape_is_refused(self):
        self.edit(lambda o: o.update(legacy_shape(o)))  # keeps aggregation_rules "2"
        code, text = self.inspect()
        self.assertEqual(code, 1)
        self.assertIn("TIMEOUT_RULE", text)
        rep = replay(self.out, self.buggy, H.PYTHON)
        self.assertFalse(rep["invariants_ok"])
        self.assertIsNone(rep["replay_outcome"])

    def test_unknown_version_is_refused_by_inspect(self):
        self.edit(lambda o: o.update({"aggregation_rules": "3"}))
        code, _ = self.inspect()
        self.assertEqual(code, 1)

    def test_a_normal_legacy_bundle_has_no_legacy_timeout_flag(self):
        self.edit(lambda o: o.pop("aggregation_rules"))
        rep = replay(self.out, self.buggy, H.PYTHON)
        self.assertEqual(rep["aggregation_rules"], "LEGACY")
        self.assertFalse(rep["legacy_timeout_semantics"])
        self.assertTrue(rep["same_outcome"])


if __name__ == "__main__":
    unittest.main()
