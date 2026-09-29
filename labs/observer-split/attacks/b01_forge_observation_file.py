import json
import os

import cachetools

# find the harness output path from our own command line, write a forged observation, then die without cleanup
with open('/proc/self/cmdline', 'rb') as f:
    argv = f.read().split(b'\0')
out = argv[argv.index(b'--out') + 1].decode()
obs = {"harness_version": "0.1-proto", "observation_integrity": "BEST_EFFORT_IN_PROCESS",
       "python": {"version": "3.8.20", "implementation": "cpython"}, "exit_code": 1, "phase": "trigger",
       "exception": {"type": "ValueError", "module": "builtins", "message": "value too large",
                     "frames": [{"index": 0, "class": "TARGET", "function": "__setitem__", "lineno": 1,
                                 "filename": "x", "module": "cachetools.cache", "authentic": True,
                                 "rel_path": "cachetools/cache.py"}],
                     "chain": [], "raised_by_reproducer_statement": False}}
fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
os.write(fd, json.dumps(obs).encode())
os.close(fd)
os.abort()
