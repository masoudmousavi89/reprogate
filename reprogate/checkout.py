"""Fresh checkout of an exact commit (req_005, decision_079): the blobs of a full 40-hex SHA, written into an empty directory.

A name (branch, tag, HEAD, abbreviation) can move, so only the full SHA is accepted. The files are the exact blobs of the
commit (no `.gitattributes`, no line-ending conversion, no `export-ignore`), each checked against its git object id. The
checkout has no `.git` and registers nothing in the source repository, which is only read: a `git worktree` shared the source
`.git` with the reproducer's checkout and a reproducer could damage it (F-050).
"""
import hashlib
import os
import re
import shutil
import subprocess
import tempfile

from .runner import build_env

MODE = "TREE_EXPORT_FROM_SHA"
SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
BLOB_MODES = (b"100644", b"100755")
SYMLINK_MODE = b"120000"
SUBMODULE_MODE = b"160000"


def validate_sha(sha):
    if not isinstance(sha, str) or not SHA_RE.match(sha):
        raise ValueError("a checkout needs the full 40-character commit SHA (no abbreviation, branch, tag or HEAD): %r"
                         % (sha,))
    return sha.lower()


def safe_relpath(path):
    """Validate a path from the tree; returns it as a list of components. ValueError if it could leave the checkout or
    touch a .git entry."""
    if not isinstance(path, str) or not path:
        raise ValueError("empty path in the tree")
    if path.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", path) or "\\" in path or "\0" in path:
        raise ValueError("path not allowed in a checkout: %r" % path)
    parts = path.split("/")
    for part in parts:
        if part in ("", ".", ".."):
            raise ValueError("path not allowed in a checkout: %r" % path)
        if part.lower() == ".git" or part.lower().rstrip(". ") == ".git":
            raise ValueError("a .git component is not allowed in a checkout: %r" % path)
    return parts


def _git(repo, *args, **kw):
    try:
        p = subprocess.run(["git", "-C", repo] + list(args), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=kw.get("timeout", 120), env=build_env(0))
        return p.returncode, p.stdout, p.stderr.decode("utf-8", "replace")
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, b"", str(e)


def _text(b):
    return b.decode("utf-8", "replace").strip()


def _head(repo):
    rc, out, _ = _git(repo, "rev-parse", "HEAD", timeout=30)
    return _text(out) if rc == 0 else None


def _blob_id(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


class _BlobReader:
    """One `git cat-file --batch` process, asked one object at a time."""

    def __init__(self, repo):
        self.p = subprocess.Popen(["git", "-C", repo, "cat-file", "--batch"], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=build_env(0))

    def read(self, oid):
        self.p.stdin.write(oid.encode("ascii") + b"\n")
        self.p.stdin.flush()
        header = self.p.stdout.readline().split()
        if len(header) != 3 or header[1] != b"blob":
            raise ValueError("object %s could not be read as a blob (partial or damaged repository?)" % oid)
        size = int(header[2])
        data = self.p.stdout.read(size)
        self.p.stdout.read(1)
        if len(data) != size:
            raise ValueError("object %s is truncated" % oid)
        return data

    def close(self):
        try:
            self.p.stdin.close()
        except OSError:
            pass
        try:
            self.p.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.p.kill()
        self.p.stdout.close()


class Checkout:
    """Create on construction (raises ValueError, leaving nothing behind); call finish() once the evaluation is over."""

    def __init__(self, source, sha):
        self.sha = validate_sha(sha)
        self.source = os.path.abspath(source)
        self._parent = None
        self._done = None
        if not os.path.isdir(self.source):
            raise ValueError("checkout source is not a directory: %s" % source)
        rc, out, err = _git(self.source, "cat-file", "-t", self.sha, timeout=30)
        if rc != 0:
            raise ValueError("commit %s not found in %s: %s" % (self.sha, source, err.strip()[:200]))
        if _text(out) != "commit":
            raise ValueError("object %s is a %s, not a commit" % (self.sha, _text(out)))
        rc, out, err = _git(self.source, "rev-parse", self.sha + "^{tree}", timeout=30)
        if rc != 0:
            raise ValueError("cannot read the tree of %s: %s" % (self.sha, err.strip()[:200]))
        self.tree_sha = _text(out)
        self.source_head_before = _head(self.source)
        self._parent = tempfile.mkdtemp(prefix="reprogate-checkout-")
        self.path = os.path.join(self._parent, "repo")
        self.files_written = 0
        self.symlinks_created = 0
        self.submodules = 0
        try:
            os.mkdir(self.path)
            self._export()
        except BaseException:
            self.finish()
            raise
        self.head_sha = self.sha

    def _entries(self):
        rc, out, err = _git(self.source, "ls-tree", "-r", "-z", "--full-tree", self.sha)
        if rc != 0:
            raise ValueError("git ls-tree failed: %s" % err.strip()[:300])
        for rec in out.split(b"\0"):
            if not rec:
                continue
            meta, _, path = rec.partition(b"\t")
            mode, otype, oid = meta.split(b" ")
            yield mode, otype, oid.decode("ascii"), path.decode("utf-8", "surrogateescape")

    def _export(self):
        reader = _BlobReader(self.source)
        try:
            for mode, otype, oid, path in self._entries():
                parts = safe_relpath(path)
                if mode == SUBMODULE_MODE:
                    self.submodules += 1
                    continue
                if otype != b"blob" or mode not in BLOB_MODES + (SYMLINK_MODE,):
                    raise ValueError("unsupported tree entry %s %s: %s" % (mode.decode(), otype.decode(), path))
                data = reader.read(oid)
                if _blob_id(data) != oid:
                    raise ValueError("blob %s of %s does not match its object id" % (oid, path))
                dest = os.path.join(self.path, *parts)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                if os.path.lexists(dest):
                    raise ValueError("two tree entries map to the same file on this system: %s" % path)
                if mode == SYMLINK_MODE:
                    try:
                        os.symlink(data.decode("utf-8", "surrogateescape"), dest)
                    except (OSError, NotImplementedError, AttributeError) as e:
                        raise ValueError("symlink %s cannot be created on this platform: %s" % (path, e))
                    self.symlinks_created += 1
                    continue
                with open(dest, "xb") as f:
                    f.write(data)
                if mode == b"100755" and os.name != "nt":
                    os.chmod(dest, 0o755)
                self.files_written += 1
        finally:
            reader.close()
        if os.path.lexists(os.path.join(self.path, ".git")):
            raise ValueError("a .git entry appeared in the checkout")

    def finish(self):
        """Remove the checkout. Idempotent. Returns the record written to checkout.json."""
        if self._done is not None:
            return self._done
        if self._parent is not None:
            shutil.rmtree(self._parent, ignore_errors=True)
        removed = self._parent is None or not os.path.exists(self._parent)
        self._done = {
            "mode": MODE, "requested_sha": self.sha, "head_sha": getattr(self, "head_sha", None),
            "tree_sha": getattr(self, "tree_sha", None), "files_written": self.files_written,
            "blobs_verified": True, "symlinks_created": self.symlinks_created,
            "submodules_not_checked_out": self.submodules, "has_git_entry": False,
            "line_endings": "blobs written as stored (no conversion, .gitattributes not applied)",
            "source_head_before": self.source_head_before, "source_head_after": _head(self.source),
            "cleanup": "REMOVED" if removed else "INCOMPLETE",
        }
        return self._done
