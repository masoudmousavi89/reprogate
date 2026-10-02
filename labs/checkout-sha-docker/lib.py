"""Small helpers for the Linux/Docker checkout lab (labs/checkout-sha-docker). Standard library only; run from the repository root."""
import hashlib
import os
import subprocess
import sys

sys.path.insert(0, os.getcwd())
from reprogate.runner import tree_hash  # noqa: E402


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo, "-c", "user.name=lab", "-c", "user.email=lab@example.invalid",
                        "-c", "core.autocrlf=false"] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.returncode, p.stdout.decode("utf-8", "replace").strip(), p.stderr.decode("utf-8", "replace").strip()


def dir_hash(root):
    """sha256 over (relative path, type, mode, content) of EVERYTHING under root, including .git, in sorted order."""
    h = hashlib.sha256()
    root = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(dirnames) + sorted(filenames):
            p = os.path.join(dirpath, name)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            if os.path.islink(p):
                h.update(("L %s -> %s\n" % (rel, os.readlink(p))).encode())
            elif os.path.isdir(p):
                h.update(("D %s\n" % rel).encode())
            else:
                with open(p, "rb") as f:
                    h.update(("F %s %o %s\n" % (rel, os.stat(p).st_mode & 0o7777, hashlib.sha256(f.read()).hexdigest())).encode())
    return h.hexdigest()


def snapshot(repo):
    """What 'the source repository is unchanged' means here: working tree, whole .git, HEAD, worktree count, ref list."""
    _, head, _ = git(repo, "rev-parse", "HEAD")
    _, wt, _ = git(repo, "worktree", "list", "--porcelain")
    _, refs, _ = git(repo, "for-each-ref", "--format=%(refname) %(objectname)")
    return {"head": head, "worktrees": wt.count("worktree "), "tree_sha256": tree_hash(repo)[0],
            "git_dir_sha256": dir_hash(os.path.join(repo, ".git")), "refs": refs.splitlines()}


def mask(text):
    home = os.path.expanduser("~")
    return text.replace(home, "<HOME>")
