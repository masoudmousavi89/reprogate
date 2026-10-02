import errno
import os
import sys

import jinja2.utils as u

target = u.__file__
repo = os.path.dirname(os.path.dirname(target))


def attempt(tag, path, flags):
    try:
        fd = os.open(path, flags)
        os.write(fd, b"x")
        os.close(fd)
        print(tag, "WROTE", path)
    except OSError as e:
        print(tag, "FAILED", errno.errorcode.get(e.errno, e.errno), path)


attempt("tracked_file", target, os.O_WRONLY | os.O_APPEND)
dot_git = os.path.join(repo, ".git")
attempt("dot_git", dot_git, os.O_WRONLY | os.O_APPEND)
fd = os.open(dot_git, os.O_RDONLY)
txt = os.read(fd, 4096).decode()
os.close(fd)
gitdir = txt.split("gitdir:", 1)[1].strip()
print("gitdir_named_in_dot_git", gitdir, "exists", os.path.exists(gitdir))
attempt("host_gitdir_HEAD", os.path.join(gitdir, "HEAD"), os.O_WRONLY | os.O_APPEND)
attempt("host_gitdir_new", os.path.join(gitdir, "pwned"), os.O_WRONLY | os.O_CREAT)
attempt("host_common_refs", os.path.join(gitdir, "..", "..", "refs", "heads", "pwned"), os.O_WRONLY | os.O_CREAT)
attempt("root_fs", "/pwned", os.O_WRONLY | os.O_CREAT)
