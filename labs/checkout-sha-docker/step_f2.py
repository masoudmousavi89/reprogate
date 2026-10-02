"""(f2) optional: tree hashes of hand-made Lab #1 checkouts (labs/jinja-843/run_lab001.sh layout), if they exist on this machine."""
import os
import sys

from lib import tree_hash

lab = sys.argv[1]
for name in ("jinja-before", "jinja-after"):
    p = os.path.join(lab, name)
    if os.path.isdir(p):
        print(name, tree_hash(p)[0][:16])
    else:
        print(name, "not present on this machine")
