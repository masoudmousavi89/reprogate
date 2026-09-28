"""End-to-end tests on a SYNTHETIC library (no network, no Docker). Runs real subprocesses."""
import os
import unittest

from reprogate import constants as C
from reprogate.evidence import verify_hashes
from reprogate.pipeline import evaluate, oracle, replay
from tests import helpers as H

FAST = dict(runs=3, timeout=20, min_completed=3)


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = H.tmpdir()
        self.buggy = H.make_repo(os.path.join(self.tmp, "buggy"))
        self.fixed = H.make_repo(os.path.join(self.tmp, "fixed"), fixed=True)
        self.claim = H.verified_claim()

    def tearDown(self):
        H.cleanup(self.tmp)

    def run_case(self, name, src, repo=None, gate=True, **kw):
        repro = H.write_repro(self.tmp, name + ".py", src)
        args = dict(FAST)
        args.update(kw)
        return evaluate(repo or self.buggy, H.PYTHON, self.claim, repro, os.path.join(self.tmp, "ev-" + name),
                        gate=gate, **args)

    # ---- the three gates from the roadmap
    def test_correct_reproducer_on_buggy_commit(self):
        o = self.run_case("good", H.GOOD_REPRO)
        self.assertEqual((o["outcome"], o["outcome_reason"]), (C.SYMPTOM_REPRODUCED, C.NONE))
        self.assertEqual(o["counts"]["matching"], 3)

    def test_correct_reproducer_on_fixed_commit_completes_cleanly(self):
        o = self.run_case("good_fixed", H.GOOD_REPRO, repo=self.fixed)
        self.assertEqual(o["outcome"], C.NO_MATCHING_REPRODUCTION_FOUND)
        self.assertEqual(o["counts"]["clean_completion_runs"], 3)

    def test_oracle_pass(self):
        repro = H.write_repro(self.tmp, "good.py", H.GOOD_REPRO)
        r = oracle(self.buggy, self.fixed, H.PYTHON, self.claim, repro, os.path.join(self.tmp, "orc"), **FAST)
        self.assertTrue(r["oracle_pass"], r)
        self.assertEqual(r["post_fix_classification"], "CLEAN_COMPLETION")

    def test_oracle_does_not_accept_broken_fix_commit(self):
        broken = H.make_repo(os.path.join(self.tmp, "brokenfix"), fixed=True, broken_import=True)
        repro = H.write_repro(self.tmp, "good.py", H.GOOD_REPRO)
        r = oracle(self.buggy, broken, H.PYTHON, self.claim, repro, os.path.join(self.tmp, "orc2"), **FAST)
        self.assertFalse(r["oracle_pass"])
        self.assertEqual(r["post_fix_classification"], "ENV_FAILURE")

    # ---- fake / gamed reproducers
    def test_direct_raise_rejected_and_never_executed(self):
        o = self.run_case("f_raise", "from minilib import Box\nraise IndexError('pop from an empty deque')\n")
        self.assertEqual((o["outcome"], o["outcome_reason"]), (C.NOT_EVALUATED, C.REPRODUCER_REJECTED))
        self.assertEqual(o["run_status"], [])

    def test_same_exception_without_target_frame(self):
        o = self.run_case("f_deque", "from collections import deque\ndeque().popleft()\n")
        self.assertEqual(o["outcome"], C.NO_MATCHING_REPRODUCTION_FOUND)

    def test_fake_traceback_on_stdout_is_ignored(self):
        src = ("from minilib import Box\nBox(1)\nprint('Traceback (most recent call last):')\n"
               "print('  File \"minilib/box.py\", line 27, in __setitem__')\n"
               "print('IndexError: pop from an empty deque')\n")
        o = self.run_case("f_stdout", src)
        self.assertEqual(o["outcome"], C.NO_MATCHING_REPRODUCTION_FOUND)
        self.assertEqual(o["counts"]["clean_completion_runs"], 3)

    def test_subclass_override_raising_from_reproducer_file(self):
        src = ("from collections import deque\nfrom minilib import Box\n\n\nclass Sneaky(Box):\n"
               "    def __setitem__(self, key, value):\n        deque().popleft()\n\n\nSneaky(1)['a'] = 1\n")
        o = self.run_case("f_subclass", src)
        self.assertEqual(o["outcome"], C.NO_MATCHING_REPRODUCTION_FOUND)

    def test_callback_trick_target_calls_back_into_reproducer(self):
        src = ("from collections import deque\nfrom minilib import Box\n\n\ndef cb(k):\n    deque().popleft()\n\n\n"
               "b = Box(1)\nb['a'] = 1\nb.each(cb)\n")
        o = self.run_case("f_callback", src)
        self.assertEqual(o["outcome"], C.NO_MATCHING_REPRODUCTION_FOUND)

    def test_forged_filename_with_fake_globals_is_not_a_target_frame(self):
        src = ("import minilib\nimport os\n"
               "p = os.path.join(os.path.dirname(minilib.__file__), 'box.py')\n"
               "exec(compile(\"raise IndexError('pop from an empty deque')\", p, 'exec'), {'__name__': 'minilib.box'})\n")
        o = self.run_case("f_forged1", src, gate=False)  # gate would already reject exec/compile
        self.assertEqual(o["outcome"], C.NO_MATCHING_REPRODUCTION_FOUND)

    def test_forged_filename_with_real_module_globals_fails_bytecode_check(self):
        src = ("import minilib\nimport minilib.box as bx\n"
               "exec(compile(\"raise IndexError('pop from an empty deque')\", bx.__file__, 'exec'), bx.__dict__)\n")
        o = self.run_case("f_forged2", src, gate=False)
        self.assertEqual(o["outcome"], C.NO_MATCHING_REPRODUCTION_FOUND)
        obs = os.path.join(self.tmp, "ev-f_forged2", "runs", "run-01", "observation.json")
        import json
        with open(obs) as fh:
            frames = json.load(fh)["exception"]["frames"]
        self.assertTrue(any(f["class"] == "FORGED_TARGET" for f in frames), frames)

    def test_repository_mutation_detected_by_tree_hash(self):
        src = ("import os\nimport minilib\n"
               "open(os.path.join(os.path.dirname(minilib.__file__), 'mutated.txt'), 'w').write('x')\n")
        o = self.run_case("f_mutate", src, gate=False)  # the gate would reject open(..., 'w')
        self.assertEqual((o["outcome"], o["outcome_reason"]), (C.INCONCLUSIVE, C.REPOSITORY_MODIFIED))

    def test_process_exit_hack_yields_no_observation(self):
        o = self.run_case("f_exit", "import os\nos._exit(0)\n", gate=False)
        self.assertEqual(o["outcome"], C.INCONCLUSIVE)
        self.assertNotEqual(o["outcome"], C.SYMPTOM_REPRODUCED)

    def test_gate_rejects_the_same_hacks_by_default(self):
        o = self.run_case("f_exit2", "import os\nos._exit(0)\n")
        self.assertEqual((o["outcome"], o["outcome_reason"]), (C.NOT_EVALUATED, C.REPRODUCER_UNSAFE))

    # ---- environment failures are not "no reproduction"
    def test_import_time_dependency_failure_is_env_failure(self):
        bad = H.make_repo(os.path.join(self.tmp, "badenv"), broken_import=True)
        o = self.run_case("good_badenv", H.GOOD_REPRO, repo=bad)
        self.assertEqual((o["outcome"], o["outcome_reason"]), (C.NOT_EVALUATED, C.ENVIRONMENT_UNAVAILABLE))

    def test_missing_interpreter_is_env_failure(self):
        repro = H.write_repro(self.tmp, "good2.py", H.GOOD_REPRO)
        o = evaluate(self.buggy, os.path.join(self.tmp, "no-such-python"), self.claim, repro,
                     os.path.join(self.tmp, "ev-nopy"), **FAST)
        self.assertEqual((o["outcome"], o["outcome_reason"]), (C.NOT_EVALUATED, C.ENVIRONMENT_UNAVAILABLE))

    def test_timeout_is_inconclusive(self):
        o = self.run_case("f_hang", "while True:\n    pass\n", runs=3, timeout=1)
        self.assertEqual((o["outcome"], o["outcome_reason"]), (C.INCONCLUSIVE, C.TIMEOUT_NOT_CLAIMED))

    # ---- provenance
    def test_unverified_provenance_refused_unless_allowed(self):
        repro = H.write_repro(self.tmp, "good3.py", H.GOOD_REPRO)
        with self.assertRaises(ValueError):
            evaluate(self.buggy, H.PYTHON, H.CLAIM, repro, os.path.join(self.tmp, "ev-up"), **FAST)
        o = evaluate(self.buggy, H.PYTHON, H.CLAIM, repro, os.path.join(self.tmp, "ev-up2"),
                     allow_unverified_provenance=True, **FAST)
        self.assertEqual(o["outcome"], C.SYMPTOM_REPRODUCED)
        self.assertEqual(o["outcome_qualifier"], "PROVENANCE_UNVERIFIED")

    def test_claim_anchor_not_in_issue_is_inferred_and_insufficient(self):
        from reprogate import provenance
        body = H.ISSUE_BODY.encode()
        claim = dict(H.CLAIM)
        # type quoted, message NOT in the issue, no location anchor -> only one weak anchor -> insufficient
        claim["anchors"] = [{"field": "exception_type", "text": "IndexError"},
                            {"field": "message", "text": "text that is NOT in the issue"}]
        frozen = provenance.check_claim(claim, body)
        self.assertFalse(frozen["anchors"][1]["found"])
        self.assertEqual(frozen["anchors"][1]["provenance"], "INFERRED")
        self.assertFalse(frozen["provenance_sufficient"])
        # type + location quoted -> sufficient
        claim["anchors"] = [{"field": "exception_type", "text": "IndexError"},
                            {"field": "location_file", "text": "minilib/box.py"}]
        self.assertTrue(provenance.check_claim(claim, body)["provenance_sufficient"])
        # type itself not in the issue -> insufficient
        claim["anchors"] = [{"field": "exception_type", "text": "TypeError"},
                            {"field": "message", "text": "pop from an empty deque"}]
        self.assertFalse(provenance.check_claim(claim, body)["provenance_sufficient"])

    # ---- evidence
    def test_bundle_hashes_detect_tampering_and_replay_matches(self):
        o = self.run_case("good_bundle", H.GOOD_REPRO)
        bundle = os.path.join(self.tmp, "ev-good_bundle")
        ok, problems = verify_hashes(bundle)
        self.assertTrue(ok, problems)
        rep = replay(bundle, self.buggy, H.PYTHON, runs=3)
        self.assertTrue(rep["same_outcome"], rep)
        with open(os.path.join(bundle, "reproducer", "good_bundle.py"), "ab") as f:
            f.write(b"# tampered\n")
        ok, problems = verify_hashes(bundle)
        self.assertFalse(ok)
        self.assertTrue(any("hash mismatch" in p for p in problems))
        self.assertEqual(o["reproducer_origin"], "AGENT_ADAPTED")
        self.assertEqual(o["observation_integrity"], "BEST_EFFORT_IN_PROCESS")


if __name__ == "__main__":
    unittest.main()
