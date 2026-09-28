"""Guard rails for the Python 3.8 target (the Lab #1 interpreter). Not a substitute for really running on 3.8."""
import ast
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAD_API = re.compile(r"\.removeprefix\(|\.removesuffix\(|functools\.cache\b|zoneinfo|math\.lcm|"
                     r"\bdict\[|\blist\[|\btuple\[|\bset\[|\)\s*->\s*\w+\s*\|\s*None|:\s*\w+\s*\|\s*None|\bmatch\s+\w+:")


def py_files():
    for base in ("reprogate", "tools"):
        for dp, _dn, fn in os.walk(os.path.join(ROOT, base)):
            for f in fn:
                if f.endswith(".py"):
                    yield os.path.join(dp, f)


class Py38Compat(unittest.TestCase):
    def test_grammar_is_3_8(self):
        for p in py_files():
            with open(p, "r", encoding="utf-8") as f:
                ast.parse(f.read(), filename=p, feature_version=(3, 8))

    def test_no_obvious_3_9_plus_apis(self):
        for p in py_files():
            with open(p, "r", encoding="utf-8") as f:
                for n, line in enumerate(f, 1):
                    code = line.split("#", 1)[0]
                    self.assertIsNone(BAD_API.search(code), "%s:%d: %s" % (p, n, line.strip()))


if __name__ == "__main__":
    unittest.main()
