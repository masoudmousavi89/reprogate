"""Result invariants (F-029): cases from labs/result-invariants, schema/enum agreement, and real bundles."""
import contextlib
import importlib.util
import io
import json
import os
import unittest

from reprogate import cli
from reprogate import constants as C
from reprogate import invariants as INV
from reprogate.evidence import write_hashes
from reprogate.invariants import validate_outcome
from reprogate.pipeline import evaluate, replay
from tests import helpers as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAST = dict(runs=3, timeout=20, min_completed=3)

PRIMARY = {
    "i01": "REASON_OUTCOME", "i02": "REASON_OUTCOME", "i03": "REASON_OUTCOME", "i04": "COUNTS_ORDER",
    "i05": "COUNTS_ORDER", "i06": "COUNTS_ORDER", "i07": "COUNTS_TOTAL", "i08": "COUNTS_TALLY",
    "i09": "ENV_LINK", "i10": "PROVENANCE", "i11": "QUALIFIER", "i12": "GATE_LINK", "i13": "ENUM",
    "i14": "MISSING_FIELD", "i15": "ORACLE", "i16": "COUNTS_ORDER",
}


def _load_cases():
    path = os.path.join(ROOT, "labs", "result-invariants", "cases.py")
    spec = importlib.util.spec_from_file_location("result_invariant_cases", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CASES = _load_cases()


class CaseTests(unittest.TestCase):
    def test_every_aggregate_branch_is_valid(self):
        self.assertEqual(len(CASES.VALID), 15)
        for cid, o in CASES.VALID:
            self.assertEqual(validate_outcome(o), [], cid)

    def test_every_impossible_mutation_is_invalid_with_its_primary_code(self):
        self.assertEqual(len(CASES.INVALID), 16)
        for cid, o in CASES.INVALID:
            codes = {x.split(":", 1)[0] for x in validate_outcome(o)}
            self.assertIn(PRIMARY[cid[:3]], codes, "%s gave %s" % (cid, sorted(codes)))

    def test_non_dict_and_non_integer_counts_do_not_crash(self):
        self.assertEqual(validate_outcome([])[0].split(":")[0], "MISSING_FIELD")
        o = CASES.mutate(CASES.base_all, counts_total="5")
        self.assertEqual(validate_outcome(o)[0].split(":")[0], "ENUM")
        o = CASES.mutate(CASES.base_all, counts_total=True)
        self.assertEqual(validate_outcome(o)[0].split(":")[0], "ENUM")

    def test_old_bundle_without_oracle_required_is_not_rejected_for_it(self):
        o = CASES.mutate(CASES.base_no)
        o.pop("oracle_required")
        self.assertEqual(validate_outcome(o), [])


class SchemaTests(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "schema", "result.schema.json"), encoding="utf-8") as f:
            self.schema = json.load(f)["properties"]

    def test_enums_equal_the_constants(self):
        self.assertEqual(set(self.schema["outcome"]["enum"]), set(INV.OUTCOMES))
        self.assertEqual(set(self.schema["outcome_reason"]["enum"]), set(INV.REASON_OUTCOME))
        self.assertEqual(set(self.schema["run_status"]["items"]["enum"]), set(INV.RUN_STATUSES))
        self.assertEqual(set(self.schema["reproducer_status"]["enum"]), set(INV.GATE_STATUSES))
        self.assertEqual(set(self.schema["claim_status"]["enum"]), set(INV.CLAIM_STATUSES))
        self.assertEqual(set(self.schema["claim_provenance"]["enum"]), set(INV.PROVENANCE_STATES))
        self.assertEqual(self.schema["outcome_qualifier"]["enum"], list(INV.QUALIFIERS))
        self.assertEqual(set(self.schema["counts"]["required"]), set(INV.COUNT_KEYS))

    def test_every_constant_reason_is_known_to_the_validator(self):
        reasons = {getattr(C, n) for n in dir(C) if n.isupper() and isinstance(getattr(C, n), str)}
        for r in INV.REASON_OUTCOME:
            self.assertIn(r, reasons)


class RealBundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = H.tmpdir()
        self.buggy = H.make_repo(os.path.join(self.tmp, "buggy"))
        self.claim = H.verified_claim()

    def tearDown(self):
        H.cleanup(self.tmp)

    def bundle(self, name, src):
        repro = H.write_repro(self.tmp, name + ".py", src)
        out = os.path.join(self.tmp, "ev-" + name)
        o = evaluate(self.buggy, H.PYTHON, self.claim, repro, out, **FAST)
        return o, out

    def test_real_outcomes_satisfy_the_invariants(self):
        for name, src in (("good", H.GOOD_REPRO),
                          ("rejected", "from minilib import Box\nraise IndexError('pop from an empty deque')\n")):
            o, _out = self.bundle(name, src)
            self.assertEqual(validate_outcome(o), [], name)

    def test_inspect_exit_code_follows_the_invariants(self):
        o, out = self.bundle("good", H.GOOD_REPRO)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["inspect", "--evidence", out]), 0)
        self._tamper(out)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["inspect", "--evidence", out]), 1)

    def test_verify_rejects_an_edited_outcome_even_when_hashes_are_regenerated(self):
        o, out = self.bundle("good", H.GOOD_REPRO)
        rep = replay(out, self.buggy, H.PYTHON)
        self.assertTrue(rep["invariants_ok"])
        self.assertTrue(rep["same_outcome"])
        self._tamper(out)
        rep = replay(out, self.buggy, H.PYTHON)
        self.assertTrue(rep["hashes_ok"])
        self.assertFalse(rep["invariants_ok"])
        self.assertIsNone(rep["replay_outcome"])
        self.assertTrue(any(x.startswith("REASON_OUTCOME") for x in rep["invariant_violations"]))

    def _tamper(self, out):
        p = os.path.join(out, "outcome.json")
        with open(p, encoding="utf-8") as f:
            doc = json.load(f)
        doc["outcome_reason"] = C.INSUFFICIENT_VALID_RUNS  # SYMPTOM_REPRODUCED cannot carry this reason
        with open(p, "w", encoding="utf-8") as f:
            json.dump(doc, f)
        write_hashes(out)


if __name__ == "__main__":
    unittest.main()
