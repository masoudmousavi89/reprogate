#!/usr/bin/env python
"""ReproGate observation harness (prototype).

Runs UNDER THE TARGET INTERPRETER, in the SAME PROCESS as the untrusted
reproducer, so the observation is BEST_EFFORT_IN_PROCESS: it raises the cost of
faking an exception, it is not a security boundary.

Python 3.8 compatible, standard library only, no imports from the reprogate package.
"""
import argparse
import ast
import json
import os
import runpy
import sys
import sysconfig
import traceback

HARNESS_VERSION = "0.1-proto"
_CODE_CACHE = {}


def _rp(p):
    try:
        return os.path.normcase(os.path.realpath(p))
    except Exception:
        return ""


def _under(path, root):
    return bool(path) and bool(root) and (path == root or path.startswith(root + os.sep))


def _stdlib_roots():
    roots = set()
    for key in ("stdlib", "platstdlib"):
        try:
            p = sysconfig.get_paths().get(key)
        except Exception:
            p = None
        if p:
            roots.add(_rp(p))
    return roots


def _classify(filename, ctx):
    if not filename:
        return "OTHER"
    if filename.startswith("<frozen"):
        return "STDLIB"
    if filename.startswith("<"):
        return "OTHER"
    rp = _rp(filename)
    if rp == ctx["repro"]:
        return "REPRODUCER"
    if rp == ctx["harness"]:
        return "HARNESS"
    parts = rp.split(os.sep)
    if "site-packages" in parts or "dist-packages" in parts:
        return "THIRDPARTY"
    for root in ctx["stdlib"]:
        if _under(rp, root):
            return "STDLIB"
    if _under(rp, ctx["repo"]):
        return "TARGET"
    return "OTHER"


def _find_code(co, name, first):
    if co.co_name == name and co.co_firstlineno == first:
        return co
    for c in co.co_consts:
        if hasattr(c, "co_code"):
            r = _find_code(c, name, first)
            if r is not None:
                return r
    return None


def _source_code_object(filename):
    if filename in _CODE_CACHE:
        return _CODE_CACHE[filename]
    try:
        with open(filename, "rb") as f:
            data = f.read()
        co = compile(data, filename, "exec", dont_inherit=True)
    except Exception:
        co = None
    _CODE_CACHE[filename] = co
    return co


def _authentic(frame):
    """Does this frame run code that really comes from the module file on disk?"""
    name = frame.f_globals.get("__name__")
    mod = sys.modules.get(name) if isinstance(name, str) else None
    if mod is None:
        return False, "module_not_in_sys_modules"
    if getattr(mod, "__dict__", None) is not frame.f_globals:
        return False, "globals_not_module_dict"
    if _rp(getattr(mod, "__file__", None) or "") != _rp(frame.f_code.co_filename):
        return False, "module_file_mismatch"
    top = _source_code_object(frame.f_code.co_filename)
    if top is None:
        return False, "source_unreadable"
    real = _find_code(top, frame.f_code.co_name, frame.f_code.co_firstlineno)
    if real is None:
        return False, "code_object_not_in_source"
    if real.co_code != frame.f_code.co_code or real.co_names != frame.f_code.co_names:
        return False, "bytecode_mismatch"
    return True, "ok"


def _rel(filename, repo_real):
    try:
        return os.path.relpath(os.path.realpath(filename), repo_real).replace("\\", "/")
    except Exception:
        return None


def _frames(tb, ctx, repo_real):
    out = []
    i = 0
    while tb is not None:
        f = tb.tb_frame
        co = f.f_code
        cls = _classify(co.co_filename, ctx)
        rec = {
            "index": i,
            "class": cls,
            "filename": co.co_filename,
            "function": co.co_name,
            "lineno": tb.tb_lineno,
            "module": f.f_globals.get("__name__"),
        }
        if cls == "TARGET":
            ok, why = _authentic(f)
            rec["authentic"] = ok
            rec["authenticity_note"] = why
            rec["rel_path"] = _rel(co.co_filename, repo_real)
            if not ok:
                rec["class"] = "FORGED_TARGET"
        out.append(rec)
        tb = tb.tb_next
        i += 1
    return out


def _safe_str(exc):
    try:
        return str(exc)
    except Exception:
        return "<unprintable exception>"


def _chain(exc, ctx, repo_real):
    out = []
    seen = set()
    via = "cause" if exc.__cause__ is not None else "context"
    cur = exc.__cause__ or exc.__context__
    while cur is not None and id(cur) not in seen and len(out) < 3:
        seen.add(id(cur))
        out.append({"type": type(cur).__name__, "message": _safe_str(cur), "via": via,
                    "frames": _frames(cur.__traceback__, ctx, repo_real)})
        via = "cause" if cur.__cause__ is not None else "context"
        cur = cur.__cause__ or cur.__context__
    return out


def _raise_lines(src):
    """Line numbers covered by `raise` statements of the reproducer source."""
    lines = set()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return lines
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise):
            lines.update(range(node.lineno, getattr(node, "end_lineno", node.lineno) + 1))
    return lines


def _raised_by_reproducer_statement(frames, src):
    """True if the innermost traceback frame is a reproducer line holding a `raise` statement (F-012)."""
    if not frames or frames[-1]["class"] != "REPRODUCER":
        return False
    return frames[-1]["lineno"] in _raise_lines(src)


def _phase(frames, src):
    first = None
    for fr in frames:
        if fr["class"] == "REPRODUCER":
            first = fr
            break
    if first is None:
        return "unknown"
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return "unknown"
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            end = getattr(node, "end_lineno", node.lineno)
            if node.lineno <= first["lineno"] <= end:
                return "import"
    return "trigger"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--repro", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pythonpath-extra", action="append", default=[])
    a = ap.parse_args(argv)

    ctx = {
        "repo": _rp(a.repo),
        "repro": _rp(a.repro),
        "harness": _rp(__file__),
        "stdlib": _stdlib_roots(),
    }
    repo_real = os.path.realpath(a.repo)
    harness_dir = os.path.dirname(ctx["harness"])
    sys.path[:] = [p for p in sys.path if _rp(p or ".") != harness_dir]
    sys.path[0:0] = [a.repo] + [os.path.join(a.repo, e) for e in a.pythonpath_extra]
    sys.argv = [a.repro]

    with open(a.repro, "rb") as f:
        src = f.read().decode("utf-8", "replace")

    exc = None
    exit_code = 0
    try:
        runpy.run_path(a.repro, run_name="__main__")
    except SystemExit as e:
        code = e.code
        if code is None:
            exit_code = 0
        elif isinstance(code, int):
            exit_code = code
        else:
            exit_code = 1
            try:
                sys.stderr.write(str(code) + "\n")
            except Exception:
                pass
    except BaseException as e:  # the whole point: observe whatever the reproducer raised
        exc = e
        exit_code = 1
        try:
            tb = e.__traceback__.tb_next if e.__traceback__ is not None else None
            traceback.print_exception(type(e), e, tb)
        except Exception:
            pass

    obs = {
        "harness_version": HARNESS_VERSION,
        "observation_integrity": "BEST_EFFORT_IN_PROCESS",
        "python": {"version": sys.version.split()[0], "implementation": sys.implementation.name},
        "exit_code": exit_code,
        "phase": None,
        "exception": None,
    }
    if exc is not None:
        frames = _frames(exc.__traceback__, ctx, repo_real)
        obs["phase"] = _phase(frames, src)
        obs["exception"] = {
            "type": type(exc).__name__,
            "module": type(exc).__module__,
            "message": _safe_str(exc),
            "frames": frames,
            "chain": _chain(exc, ctx, repo_real),
            "raised_by_reproducer_statement": _raised_by_reproducer_statement(frames, src),
        }
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:
        pass
    try:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(obs, f)
    except Exception as e:
        sys.stderr.write("harness.py: cannot write observation: %s\n" % e)
        return 70
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
