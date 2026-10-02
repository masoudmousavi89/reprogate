"""Fresh checkout of an exact commit (req_005): a detached `git worktree` created from a full 40-hex SHA.

A name (branch, tag, HEAD, abbreviation) can move, so only the full SHA is accepted. The worktree lives in a temp
directory outside the evidence bundle and is removed after the evaluation (also when it raises). A worktree shares the
source repository's `.git`; see labs/checkout-sha/PREDICTIONS.md for what that means in host mode.
"""
import os
import re
import shutil
import tempfile

from .runner import _run_small

MODE = "WORKTREE_DETACHED_FROM_SHA"
SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def validate_sha(sha):
    if not isinstance(sha, str) or not SHA_RE.match(sha):
        raise ValueError("a checkout needs the full 40-character commit SHA (no abbreviation, branch, tag or HEAD): %r"
                         % (sha,))
    return sha.lower()


def _git(repo, *args):
    # core.autocrlf=false: the tool must evaluate the bytes of the commit, not a platform-converted copy (a Git for
    # Windows with the usual system setting core.autocrlf=true would otherwise write CRLF into the worktree)
    return _run_small(["git", "-c", "core.autocrlf=false", "-C", repo] + list(args), timeout=120)


def _head(repo):
    rc, out, _ = _git(repo, "rev-parse", "HEAD")
    return out.strip() if rc == 0 else None


def _worktrees(repo):
    rc, out, _ = _git(repo, "worktree", "list", "--porcelain")
    return len([l for l in out.splitlines() if l.startswith("worktree ")]) if rc == 0 else None


class Checkout:
    """Create on construction (raises ValueError, leaving nothing behind); call finish() once the evaluation is over."""

    def __init__(self, source, sha):
        self.sha = validate_sha(sha)
        self.source = os.path.abspath(source)
        self._parent = None
        self._done = None
        if not os.path.isdir(self.source):
            raise ValueError("checkout source is not a directory: %s" % source)
        rc, out, err = _git(self.source, "cat-file", "-t", self.sha)
        if rc != 0:
            raise ValueError("commit %s not found in %s: %s" % (self.sha, source, err.strip()[:200]))
        if out.strip() != "commit":
            raise ValueError("object %s is a %s, not a commit" % (self.sha, out.strip()))
        self.source_head_before = _head(self.source)
        self.worktrees_before = _worktrees(self.source)
        self._parent = tempfile.mkdtemp(prefix="reprogate-checkout-")
        self.path = os.path.join(self._parent, "repo")
        try:
            rc, _, err = _git(self.source, "worktree", "add", "--detach", self.path, self.sha)
            if rc != 0:
                raise ValueError("git worktree add failed: %s" % err.strip()[:300])
            head = _head(self.path)
            if head != self.sha:
                raise ValueError("checkout HEAD %s is not the requested commit %s" % (head, self.sha))
            rc, st, err = _git(self.path, "status", "--porcelain")
            if rc != 0 or st.strip():
                raise ValueError("fresh checkout is not clean: %s" % (st.strip() or err.strip())[:300])
        except BaseException:
            self.finish()
            raise
        self.head_sha = head

    def finish(self):
        """Remove the worktree. Idempotent. Returns the record written to checkout.json."""
        if self._done is not None:
            return self._done
        if self._parent is not None:
            if os.path.isdir(getattr(self, "path", "") or ""):
                _git(self.source, "worktree", "remove", "--force", self.path)
            shutil.rmtree(self._parent, ignore_errors=True)
            _git(self.source, "worktree", "prune")
        removed = self._parent is None or not os.path.exists(self._parent)
        after = _worktrees(self.source)
        self._done = {
            "mode": MODE, "requested_sha": self.sha, "head_sha": getattr(self, "head_sha", None), "clean": True,
            "line_endings": "core.autocrlf=false (bytes of the commit; .gitattributes eol rules still apply)",
            "source_head_before": self.source_head_before, "source_head_after": _head(self.source),
            "source_worktrees_before": self.worktrees_before, "source_worktrees_after": after,
            "cleanup": "REMOVED" if removed and after == self.worktrees_before else "INCOMPLETE",
        }
        return self._done
