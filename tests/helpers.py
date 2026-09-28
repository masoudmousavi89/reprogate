"""Synthetic target library that reproduces the shape of jinja#843, used by the tests."""
import os
import shutil
import sys
import tempfile
import textwrap

from reprogate import provenance

BOX_BUGGY = '''
from collections import deque


class Box(object):
    def __init__(self, capacity):
        self.capacity = capacity
        self._mapping = {}
        self._queue = deque()
        self._postinit()

    def _postinit(self):
        self._popleft = self._queue.popleft
        self._append = self._queue.append

    def copy(self):
        rv = self.__class__(self.capacity)
        rv._mapping.update(self._mapping)
        rv._queue = %s
        return rv

    def each(self, fn):
        for k in list(self._mapping):
            fn(k)

    def __setitem__(self, key, value):
        if key not in self._mapping and len(self._mapping) >= self.capacity:
            del self._mapping[self._popleft()]
        self._append(key)
        self._mapping[key] = value
'''

BUGGY_COPY = "deque(self._queue)"
FIXED_COPY = "rv._queue; rv._queue.extend(self._queue)"

ISSUE_BODY = (
    "Copying a Box then adding an item crashes.\r\n\r\n```\r\n"
    ">>> b = box.Box(1)\r\n>>> b['foo'] = 'bar'\r\n>>> c = b.copy()\r\n>>> c['blah'] = 'blargh'\r\n"
    "Traceback (most recent call last):\r\n  File \"minilib/box.py\", line 27, in __setitem__\r\n"
    "    del self._mapping[self._popleft()]\r\nIndexError: pop from an empty deque\r\n```\r\n"
)

CLAIM = {
    "schema_version": "0.1-proto",
    "issue": {"number": 1},
    "claim": {"kind": "exception", "exception_type": "IndexError", "message": "pop from an empty deque",
              "location": {"file": "minilib/box.py", "function": "__setitem__"}},
    "anchors": [
        {"field": "exception_type", "text": "IndexError"},
        {"field": "message", "text": "pop from an empty deque"},
        {"field": "location_file", "text": "minilib/box.py"},
        {"field": "location_function", "text": "__setitem__"},
    ],
}

GOOD_REPRO = b"""from minilib import Box

b = Box(1)
b['foo'] = 'bar'
c = b.copy()
c['blah'] = 'blargh'
print("OK", list(c._mapping))
"""


def make_repo(root, fixed=False, broken_import=False):
    pkg = os.path.join(root, "minilib")
    os.makedirs(pkg)
    box = BOX_BUGGY % ("None" if fixed else BUGGY_COPY)
    if fixed:
        box = box.replace("rv._queue = None", "rv._queue.extend(self._queue)")
    with open(os.path.join(pkg, "box.py"), "w") as f:
        f.write(box)
    init = "from .box import Box\n"
    if broken_import:
        init = "import definitely_missing_dependency_xyz\n" + init
    with open(os.path.join(pkg, "__init__.py"), "w") as f:
        f.write(init)
    return root


def verified_claim():
    return provenance.check_claim(CLAIM, ISSUE_BODY.encode("utf-8"))


def tmpdir():
    return tempfile.mkdtemp(prefix="rg-test-")


def cleanup(d):
    shutil.rmtree(d, ignore_errors=True)


def write_repro(d, name, src):
    p = os.path.join(d, name)
    with open(p, "wb") as f:
        f.write(src if isinstance(src, bytes) else src.encode("utf-8"))
    return p


PYTHON = sys.executable
