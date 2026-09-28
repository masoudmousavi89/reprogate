"""Static reproducer gate (first line of defence, NOT a security boundary).

The gate reads the reproducer as text/AST and never executes it.
Status precedence: UNSAFE > REJECTED > NOT_AUDITABLE > VALID.
"""
import ast

from .constants import GATE_NOT_AUDITABLE, GATE_REJECTED, GATE_UNSAFE, GATE_VALID
from .util import sha256_bytes

MAX_BYTES = 4096
MAX_LINES = 80
MAX_LINE_LEN = 200

UNSAFE_CODES = {"UNSAFE_MODULE", "TRACING", "FRAME_INTROSPECTION", "PROCESS_OR_FILE_OPERATION"}
AUDIT_CODES = {"TOO_LARGE", "TOO_MANY_LINES", "LINE_TOO_LONG"}

FORBIDDEN_CALLS = {
    "eval": "DYNAMIC_CODE",
    "exec": "DYNAMIC_CODE",
    "compile": "DYNAMIC_CODE",
    "__import__": "DYNAMIC_IMPORT",
    "setattr": "PATCHES_TARGET",
    "delattr": "PATCHES_TARGET",
}
FORBIDDEN_MODULES = {
    "ctypes": "UNSAFE_MODULE",
    "subprocess": "UNSAFE_MODULE",
    "shutil": "UNSAFE_MODULE",
    "socket": "UNSAFE_MODULE",
    "multiprocessing": "UNSAFE_MODULE",
    "builtins": "UNSAFE_MODULE",
    "importlib": "DYNAMIC_IMPORT",
    "mock": "MOCKING",
    "unittest.mock": "MOCKING",
}
FORBIDDEN_ATTRS = {
    ("sys", "settrace"): "TRACING",
    ("sys", "setprofile"): "TRACING",
    ("sys", "modules"): "PATCHES_TARGET",
    ("sys", "_getframe"): "FRAME_INTROSPECTION",
    ("os", "system"): "PROCESS_OR_FILE_OPERATION",
    ("os", "popen"): "PROCESS_OR_FILE_OPERATION",
    ("os", "_exit"): "PROCESS_OR_FILE_OPERATION",
    ("os", "kill"): "PROCESS_OR_FILE_OPERATION",
    ("os", "remove"): "PROCESS_OR_FILE_OPERATION",
    ("os", "unlink"): "PROCESS_OR_FILE_OPERATION",
    ("os", "rename"): "PROCESS_OR_FILE_OPERATION",
    ("os", "rmdir"): "PROCESS_OR_FILE_OPERATION",
    ("os", "removedirs"): "PROCESS_OR_FILE_OPERATION",
}
FORBIDDEN_NAMES = {
    "monkeypatch": "MOCKING",
    "mocker": "MOCKING",
    "patch": "MOCKING",
    "Mock": "MOCKING",
    "MagicMock": "MOCKING",
    "FunctionType": "DYNAMIC_CODE",
    "CodeType": "DYNAMIC_CODE",
}
DUNDER_ATTRS = {"__code__", "__globals__", "__builtins__", "__closure__", "__subclasses__"}
WRITE_ATTRS = {"write_text", "write_bytes", "unlink", "rmdir", "rename", "touch", "truncate"}


class _Visitor(ast.NodeVisitor):
    def __init__(self):
        self.findings = []
        self.imported = set()
        self.scopes = []  # "func" | "class" | "except", innermost last

    def add(self, code, node, detail):
        self.findings.append({"code": code, "line": getattr(node, "lineno", 0), "detail": detail})

    def _module(self, name, node):
        if name in FORBIDDEN_MODULES:
            self.add(FORBIDDEN_MODULES[name], node, "import of " + name)
        else:
            top = name.split(".")[0]
            if top in FORBIDDEN_MODULES:
                self.add(FORBIDDEN_MODULES[top], node, "import of " + name)

    def visit_Import(self, node):
        for a in node.names:
            self._module(a.name, node)
            self.imported.add((a.asname or a.name).split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        mod = node.module or ""
        self._module(mod, node)
        for a in node.names:
            self._module((mod + "." + a.name) if mod else a.name, node)
            self.imported.add(a.asname or a.name)
        self.generic_visit(node)

    def visit_Raise(self, node):
        # F-011: a raise inside a function body is a legitimate callback trigger (the matcher's origin
        # rule still rejects reproducer frames after the first target frame). Module level, class body
        # and except handlers (catch-and-reraise) stay rejected.
        if not self.scopes or self.scopes[-1] != "func" or "except" in self.scopes:
            self.add("DIRECT_RAISE", node, "reproducer raises an exception itself outside a function body")
        self.generic_visit(node)

    def _scoped(self, kind, node):
        self.scopes.append(kind)
        self.generic_visit(node)
        self.scopes.pop()

    def visit_FunctionDef(self, node):
        self._scoped("func", node)

    def visit_AsyncFunctionDef(self, node):
        self._scoped("func", node)

    def visit_ClassDef(self, node):
        self._scoped("class", node)

    def visit_ExceptHandler(self, node):
        self._scoped("except", node)

    def visit_Call(self, node):
        fn = node.func
        if isinstance(fn, ast.Name):
            if fn.id in FORBIDDEN_CALLS:
                self.add(FORBIDDEN_CALLS[fn.id], node, "call to " + fn.id)
            if fn.id == "open":
                self._open(node)
        elif isinstance(fn, ast.Attribute):
            if fn.attr in WRITE_ATTRS:
                self.add("PROCESS_OR_FILE_OPERATION", node, "call to ." + fn.attr)
        self.generic_visit(node)

    def _open(self, node):
        mode = None
        if len(node.args) >= 2:
            mode = node.args[1]
        for kw in node.keywords:
            if kw.arg == "mode":
                mode = kw.value
        if mode is None:
            return
        if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
            if any(c in mode.value for c in "wax+"):
                self.add("PROCESS_OR_FILE_OPERATION", node, "open() in a writing mode")
        else:
            self.add("PROCESS_OR_FILE_OPERATION", node, "open() with a non-constant mode")

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            key = (node.value.id, node.attr)
            if key in FORBIDDEN_ATTRS:
                self.add(FORBIDDEN_ATTRS[key], node, "use of %s.%s" % key)
        if node.attr in DUNDER_ATTRS:
            self.add("DYNAMIC_CODE", node, "access to " + node.attr)
        self.generic_visit(node)

    def visit_Name(self, node):
        if node.id in FORBIDDEN_NAMES:
            self.add(FORBIDDEN_NAMES[node.id], node, "use of name " + node.id)
        self.generic_visit(node)

    def visit_arg(self, node):
        if node.arg in FORBIDDEN_NAMES:
            self.add(FORBIDDEN_NAMES[node.arg], node, "parameter named " + node.arg)
        self.generic_visit(node)

    def _target(self, t, node):
        if isinstance(t, (ast.Tuple, ast.List)):
            for e in t.elts:
                self._target(e, node)
            return
        base = t
        while isinstance(base, (ast.Attribute, ast.Subscript)):
            base = base.value
        if isinstance(t, (ast.Attribute, ast.Subscript)) and isinstance(base, ast.Name):
            if base.id in self.imported and isinstance(t, ast.Attribute):
                self.add("PATCHES_TARGET", node, "assignment to attribute of imported name " + base.id)

    def visit_Assign(self, node):
        for t in node.targets:
            self._target(t, node)
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        self._target(node.target, node)
        self.generic_visit(node)

    def visit_Delete(self, node):
        for t in node.targets:
            self._target(t, node)
        self.generic_visit(node)


def gate_source(data):
    """Inspect reproducer bytes. Returns a JSON-serialisable dict."""
    findings = []
    sha = sha256_bytes(data)
    if len(data) > MAX_BYTES:
        findings.append({"code": "TOO_LARGE", "line": 0, "detail": "%d bytes > %d" % (len(data), MAX_BYTES)})
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return {"status": GATE_REJECTED, "reproducer_sha256": sha,
                "findings": findings + [{"code": "NOT_UTF8", "line": 0, "detail": "not valid UTF-8"}]}
    lines = text.splitlines()
    if len(lines) > MAX_LINES:
        findings.append({"code": "TOO_MANY_LINES", "line": 0, "detail": "%d lines > %d" % (len(lines), MAX_LINES)})
    for i, ln in enumerate(lines, 1):
        if len(ln) > MAX_LINE_LEN:
            findings.append({"code": "LINE_TOO_LONG", "line": i, "detail": "%d chars" % len(ln)})
            break
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        return {"status": GATE_REJECTED, "reproducer_sha256": sha,
                "findings": findings + [{"code": "SYNTAX_ERROR", "line": e.lineno or 0, "detail": str(e.msg)}]}
    v = _Visitor()
    v.visit(tree)
    findings.extend(v.findings)
    codes = {f["code"] for f in findings}
    if codes & UNSAFE_CODES:
        status = GATE_UNSAFE
    elif codes - AUDIT_CODES:
        status = GATE_REJECTED
    elif codes & AUDIT_CODES:
        status = GATE_NOT_AUDITABLE
    else:
        status = GATE_VALID
    return {"status": status, "reproducer_sha256": sha, "findings": findings}
