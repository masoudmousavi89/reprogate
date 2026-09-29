"""Pure helpers of the v3 sample tools (labs/sample-v3/PROTOCOL.md); no network."""
import importlib.util
import os
import random
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "tools", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


POOL = _load("pypi_pool")
SAMPLER = _load("sample_issues")


class WheelTagTests(unittest.TestCase):
    def test_py3_none_any(self):
        self.assertTrue(POOL.py3_none_any("six-1.16.0-py2.py3-none-any.whl"))
        self.assertTrue(POOL.py3_none_any("attrs-23.1.0-py3-none-any.whl"))
        self.assertTrue(POOL.py3_none_any("pkg-1.0-1-py3-none-any.whl"))  # with a build tag
        self.assertFalse(POOL.py3_none_any("numpy-1.26.0-cp311-cp311-manylinux_2_17_x86_64.whl"))
        self.assertFalse(POOL.py3_none_any("pkg-1.0-py2-none-any.whl"))
        self.assertFalse(POOL.py3_none_any("pkg-1.0-py3-abi3-any.whl"))
        self.assertFalse(POOL.py3_none_any("pkg-1.0.tar.gz"))


class GithubRepoTests(unittest.TestCase):
    def test_key_order_and_skipped_owners(self):
        info = {"project_urls": {"Funding": "https://github.com/sponsors/someone",
                                 "Homepage": "https://github.com/home/page",
                                 "Source": "https://github.com/owner/repo.git"},
                "home_page": "https://github.com/other/one"}
        self.assertEqual(POOL.github_repo(info), "owner/repo")

    def test_remaining_keys_sorted_then_home_page(self):
        info = {"project_urls": {"Zeta": "https://example.org", "Changelog": "https://github.com/a/b/blob/main/CHANGES"}}
        self.assertEqual(POOL.github_repo(info), "a/b")
        self.assertEqual(POOL.github_repo({"project_urls": {"Funding": "https://github.com/sponsors/x"},
                                           "home_page": "https://github.com/c/d"}), "c/d")
        self.assertIsNone(POOL.github_repo({"project_urls": {"Docs": "https://docs.example.org"}}))

    def test_classify_reasons(self):
        self.assertEqual(POOL.classify("x", None), (None, "NOT_ON_PYPI"))
        doc = {"urls": [{"filename": "x-1.0.tar.gz"}], "info": {"version": "1.0"}}
        self.assertEqual(POOL.classify("x", doc), (None, "NO_PY3_NONE_ANY_WHEEL"))
        doc["urls"].append({"filename": "x-1.0-py3-none-any.whl"})
        self.assertEqual(POOL.classify("x", doc), (None, "NO_GITHUB_REPO"))
        doc["info"]["project_urls"] = {"Source": "https://github.com/o/x"}
        entry, reason = POOL.classify("x", doc)
        self.assertIsNone(reason)
        self.assertEqual(entry["repo"], "o/x")


class NarrowPickTests(unittest.TestCase):
    def test_excluded_repository_is_recorded_without_a_search(self):
        called = []
        orig = SAMPLER.search
        SAMPLER.search = lambda *a: called.append(a) or {"total_count": 0}
        try:
            pkgs = [{"project": "p", "rank": 1, "repo": "Pallets/Jinja"}]
            meta, flag, item = SAMPLER.pick_narrow(random.Random(1), pkgs, {"pallets/jinja"})
            self.assertEqual((flag, item), ("EXCLUDED", None))
            self.assertEqual(called, [])
            meta, flag, item = SAMPLER.pick_narrow(random.Random(1), pkgs, set())
            self.assertEqual((flag, item, meta["total"]), (None, None, 0))
            self.assertEqual(len(called), 1)
        finally:
            SAMPLER.search = orig


if __name__ == "__main__":
    unittest.main()
