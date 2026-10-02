"""(b) what the container sees: same mounts as reprogate/runner.py (read from the code, not guessed)."""
import json
import os
import subprocess
import sys

from lib import mask
from reprogate import sandbox as sbx
from reprogate.checkout import Checkout
from reprogate.runner import HARNESS

src, image = sys.argv[1], sys.argv[2]
B = "81825095d24f4dbccb40f787fff70db54989b91c"
PROBE = r'''
import errno, json, os, shutil
r = {}
r["git_binary"] = shutil.which("git")
with open("/repo/.git", "rb") as f:
    r["dot_git_is_file"] = os.path.isfile("/repo/.git")
    txt = f.read().decode()
r["dot_git_content"] = txt.strip()
gd = txt.split("gitdir:", 1)[1].strip()
r["gitdir_exists_in_container"] = os.path.exists(gd)
def w(path, flags):
    try:
        fd = os.open(path, flags); os.write(fd, b"x"); os.close(fd); return "WROTE"
    except OSError as e:
        return "FAILED " + errno.errorcode.get(e.errno, str(e.errno))
r["write_tracked_file"] = w("/repo/jinja2/utils.py", os.O_WRONLY | os.O_APPEND)
r["write_dot_git"] = w("/repo/.git", os.O_WRONLY | os.O_APPEND)
r["create_in_repo"] = w("/repo/new.txt", os.O_WRONLY | os.O_CREAT)
r["write_host_gitdir_HEAD"] = w(gd + "/HEAD", os.O_WRONLY | os.O_APPEND)
r["create_host_path"] = w(gd + "/pwned", os.O_WRONLY | os.O_CREAT)
r["create_in_root"] = w("/pwned", os.O_WRONLY | os.O_CREAT)
r["mount_options_repo"] = [l.split()[3] for l in open("/proc/mounts") if l.split()[1] == "/repo"]
print(json.dumps(r, indent=1))
'''
co = Checkout(src, B)
try:
    mounts = [(co.path, "/repo", "ro"), (HARNESS, "/rg/harness.py", "ro")]
    sb = sbx.make(image)
    cmd = sbx.run_prefix(sb, sbx.new_name(), mounts, {}) + ["python", "-c", PROBE]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("docker run rc", p.returncode)
    print(mask(p.stdout.decode()).replace(co.path, "<WORKTREE>"))
    print(mask(p.stderr.decode()[-300:]))
    # an image with git, if one can be pulled from the mirror (the python image has none)
    gimg = "mirror.gcr.io/alpine/git:latest"
    pull = subprocess.run(["docker", "pull", "-q", gimg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if pull.returncode != 0:
        print("git image not available (%s): %s" % (gimg, mask(pull.stdout.decode().strip()[-200:])))
    else:
        sb2 = sbx.make(gimg)
        cmd = sbx.run_prefix(sb2, sbx.new_name(), mounts, {}) + ["git", "-c", "safe.directory=/repo", "-C", "/repo", "status"]
        # alpine/git has an entrypoint "git"; override it so the command above is the whole command line
        cmd.insert(cmd.index(gimg), "--entrypoint")
        cmd.insert(cmd.index(gimg), "")
        p2 = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print("git -C /repo status in the container: rc", p2.returncode, mask(p2.stdout.decode().replace(co.path, "<WORKTREE>").strip()[-300:]))
finally:
    print("finish:", co.finish()["cleanup"])
