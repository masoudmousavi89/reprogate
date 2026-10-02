"""(e, static) which reproducer files under labs/ contain file-writing calls; classified as lab reproducer/fixture or deliberate attack/probe."""
import ast
import glob
import os
import sys

ATTACK_DIRS = ("labs/adversarial-round3", "labs/checkout-sha-docker", "labs/checkout-export-linux", "labs/gate-round2", "labs/observer-split",
               "labs/wrong-output", "labs/provenance-guard", "labs/result-invariants", "labs/claim-hash", "labs/fresh-env", "labs/incomplete-bundle",
               "labs/bundle-structure", "labs/reproducer-origin", "labs/sample-v3")
WRITE_FLAGS = ("WRONLY", "RDWR", "CREAT", "APPEND", "TRUNC")


def findings(path):
    try:
        tree = ast.parse(open(path, "rb").read())
    except SyntaxError:
        return ["unparsable"]
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
        if name == "open" and isinstance(f, ast.Name):
            mode = None
            if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                mode = n.args[1].value
            for k in n.keywords:
                if k.arg == "mode" and isinstance(k.value, ast.Constant):
                    mode = k.value.value
            if isinstance(mode, str) and any(c in mode for c in "wax+"):
                out.append("open(mode=%r)@%d" % (mode, n.lineno))
        elif name == "open" and isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == "os":
            src = ast.dump(n)
            if any(fl in src for fl in WRITE_FLAGS):
                out.append("os.open(write flags)@%d" % n.lineno)
        elif name in ("write_text", "write_bytes"):
            out.append("%s@%d" % (name, n.lineno))
        elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
            if (f.value.id == "shutil" and name in ("copyfile", "copy", "copy2", "copytree", "rmtree", "move")) or \
               (f.value.id == "os" and name in ("makedirs", "mkdir", "rename", "replace", "remove", "unlink", "symlink", "truncate")):
                out.append("%s.%s@%d" % (f.value.id, name, n.lineno))
    return out


SKIP_PARTS = ("/evidence-", "/runs/", "/reproducer/", "/out-", "/.venv")
files = sorted(f for f in set(glob.glob("labs/**/repro*.py", recursive=True) + glob.glob("labs/**/fixtures/*.py", recursive=True) + glob.glob("labs/**/attacks/*.py", recursive=True)
                   + glob.glob("labs/adversarial-round3/d0*.py") + glob.glob("labs/checkout-*/probe_*.py")) if not any(x in "/" + f for x in SKIP_PARTS))
lab, att = [], []
for f in files:
    fi = findings(f)
    (att if f.startswith(ATTACK_DIRS) else lab).append((f, fi))
print("reproducer/fixture files scanned:", len(files), "| lab reproducers and fixtures:", len(lab), "| deliberate attack or probe files:", len(att))
print("lab reproducers/fixtures with file-writing calls:", [(f, fi) for f, fi in lab if fi] or "none")
print("deliberate attack/probe files with file-writing calls:", sum(1 for f, fi in att if fi), "of", len(att))
