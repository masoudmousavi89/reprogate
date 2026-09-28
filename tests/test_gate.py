"""The gate is tested on TEXT ONLY: none of these snippets is ever executed."""
import unittest

from reprogate.gate import gate_source


def codes(src):
    r = gate_source(src.encode("utf-8"))
    return r["status"], {f["code"] for f in r["findings"]}


class GateTests(unittest.TestCase):
    def test_clean_reproducer_is_valid(self):
        st, c = codes("from minilib import Box\nb = Box(1)\nb['a'] = 1\nb.copy()\n")
        self.assertEqual((st, c), ("VALID", set()))

    def test_direct_raise_rejected(self):
        st, c = codes("raise IndexError('x')\n")
        self.assertEqual(st, "REJECTED")
        self.assertIn("DIRECT_RAISE", c)

    def test_dynamic_code_rejected(self):
        for src in ("exec('1')\n", "eval('1')\n", "compile('1','f','exec')\n", "__import__('os')\n"):
            st, _ = codes(src)
            self.assertEqual(st, "REJECTED", src)

    def test_mocking_and_patching_rejected(self):
        for src in ("from unittest import mock\n", "import mock\n", "def t(monkeypatch):\n    pass\n",
                    "import minilib\nminilib.Box.copy = None\n", "setattr(object, 'x', 1)\n",
                    "from minilib import Box\nBox.copy = None\n"):
            st, _ = codes(src)
            self.assertIn(st, ("REJECTED", "UNSAFE"), src)

    def test_unsafe_constructs(self):
        for src in ("import ctypes\n", "import subprocess\n", "import sys\nsys.settrace(None)\n",
                    "import os\nos._exit(0)\n", "import os\nos.system('x')\n", "import sys\nsys._getframe()\n"):
            st, _ = codes(src)
            self.assertEqual(st, "UNSAFE", src)

    def test_file_writes_flagged(self):
        for src in ("open('x', 'w')\n", "open('x', mode='a')\n", "import pathlib\npathlib.Path('x').write_text('y')\n",
                    "m = 'w'\nopen('x', m)\n"):
            st, _ = codes(src)
            self.assertEqual(st, "UNSAFE", src)
        self.assertEqual(codes("open('x')\n")[0], "VALID")
        self.assertEqual(codes("open('x', 'r')\n")[0], "VALID")

    def test_introspection_flagged(self):
        st, _ = codes("def f(): pass\nf.__code__\n")
        self.assertEqual(st, "REJECTED")

    def test_auditability_limits(self):
        self.assertEqual(gate_source(("x = 1\n" * 200).encode())["status"], "NOT_AUDITABLE")
        self.assertEqual(gate_source(("x = '" + "a" * 300 + "'\n").encode())["status"], "NOT_AUDITABLE")

    def test_syntax_error_and_encoding(self):
        self.assertEqual(gate_source(b"def (:\n")["status"], "REJECTED")
        self.assertEqual(gate_source(b"\xff\xfe\x00")["status"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
