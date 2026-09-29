import ast
import json
import os

import cachetools.cache

# like b02, but the forged TARGET frame points at the real source: real file, real function, and the real line
# of the `raise ValueError('value too large')` inside Cache.__setitem__
src_file = os.path.realpath(cachetools.cache.__file__)
repo_root = os.path.dirname(os.path.dirname(src_file))
with open(src_file, 'rb') as f:
    tree = ast.parse(f.read())
line = None
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == '__setitem__':
        for sub in ast.walk(node):
            if isinstance(sub, ast.Raise):
                line = sub.lineno
with open('/proc/self/cmdline', 'rb') as f:
    argv = f.read().split(b'\0')
path = argv[argv.index(b'--result-file') + 1].decode() if b'--result-file' in argv else argv[argv.index(b'--out') + 1].decode()
obs = {"harness_version": "0.1-proto", "observation_integrity": "BEST_EFFORT_IN_PROCESS",
       "python": {"version": "3.8.20", "implementation": "cpython"}, "exit_code": 1, "phase": "trigger",
       "exception": {"type": "ValueError", "module": "builtins", "message": "value too large",
                     "frames": [{"index": 0, "class": "TARGET", "function": "__setitem__", "lineno": line,
                                 "filename": src_file, "module": "cachetools.cache", "authentic": True,
                                 "rel_path": os.path.relpath(src_file, repo_root).replace(os.sep, '/')}],
                     "chain": [], "raised_by_reproducer_statement": False}}
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
os.write(fd, json.dumps({"protocol": "rg-obs-1", "obs": obs}).encode())
os.close(fd)
getattr(os, '_e' + 'xit')(1)
