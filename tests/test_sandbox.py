"""Docker sandbox tests (F-017). Skipped when Docker or the test image is not available.

Set REPROGATE_TEST_IMAGE to a Python 3.8+ image already present locally (default: mirror.gcr.io/library/python:3.8-slim).
"""
import os
import subprocess
import unittest

from reprogate import constants as C
from reprogate import sandbox as sbx
from reprogate.pipeline import evaluate
from reprogate.runner import run_once
from tests import helpers as H

IMAGE = os.environ.get("REPROGATE_TEST_IMAGE", "mirror.gcr.io/library/python:3.8-slim")


def docker_ready():
    try:
        return subprocess.run(["docker", "image", "inspect", IMAGE], stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, timeout=30).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


class CommandShapeTests(unittest.TestCase):
    def test_run_prefix_has_the_isolation_flags(self):
        cmd = sbx.run_prefix(sbx.make("img"), "n", [("/a", "/repo", "ro")], {"PYTHONHASHSEED": "1"})
        for flag in ("--network", "none", "--read-only", "--cap-drop", "ALL", "no-new-privileges",
                     "--pids-limit", "--memory", "65534:65534", "/a:/repo:ro", "PYTHONHASHSEED=1"):
            self.assertIn(flag, cmd)
        self.assertEqual(cmd[-1], "img")

    def test_work_and_tmp_are_writable_for_the_unprivileged_user(self):  # F-051
        cmd = sbx.run_prefix(sbx.make("img"), "n")
        self.assertIn("/work:rw,size=64m,noexec,nosuid,mode=1777", cmd)
        self.assertIn("/tmp:rw,size=64m,noexec,nosuid", cmd)
        self.assertEqual(cmd.count("--tmpfs"), 2)


@unittest.skipUnless(docker_ready(), "docker or test image not available")
class DockerSandboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = H.tmpdir()
        self.repo = H.make_repo(os.path.join(self.tmp, "buggy"))
        self.sb = sbx.make(IMAGE)

    def tearDown(self):
        H.cleanup(self.tmp)

    def raw(self, name, src, timeout=20):
        run_dir = os.path.join(self.tmp, name)
        return run_once("python", self.repo, src.encode("utf-8"), run_dir, timeout, 1, sandbox=self.sb)

    def test_good_reproducer_reproduces_inside_container(self):
        o = evaluate(self.repo, "python", H.verified_claim(), H.write_repro(self.tmp, "good.py", H.GOOD_REPRO),
                     os.path.join(self.tmp, "ev"), runs=3, timeout=30, min_completed=3, sandbox=self.sb)
        self.assertEqual((o["outcome"], o["outcome_reason"]), (C.SYMPTOM_REPRODUCED, C.NONE))
        self.assertEqual(o["sandbox"]["kind"], "DOCKER")
        self.assertTrue(o["sandbox"]["image_id"])

    def test_network_is_unreachable(self):
        r = self.raw("net", "import socket\ntry:\n    socket.create_connection(('1.1.1.1', 80), 3)\n    print('NET-OK')\n"
                            "except OSError as e:\n    print('NET-BLOCKED')\n")
        self.assertIn(b"NET-BLOCKED", r["stdout"])

    def test_repository_and_root_are_read_only(self):
        r = self.raw("ro", "for p in ('/repo/x.txt', '/etc/x.txt'):\n    try:\n        open(p, 'w')\n"
                           "        print('WROTE', p)\n    except OSError:\n        print('DENIED', p)\n")
        self.assertIn(b"DENIED /repo/x.txt", r["stdout"])
        self.assertIn(b"DENIED /etc/x.txt", r["stdout"])
        self.assertNotIn(b"WROTE", r["stdout"])

    def test_runs_as_non_root(self):
        r = self.raw("uid", "import os\nprint('UID', os.getuid())\n")
        self.assertIn(b"UID 65534", r["stdout"])

    def test_timeout_kills_the_container(self):
        r = self.raw("loop", "while True:\n    pass\n", timeout=4)
        self.assertTrue(r["timed_out"])
        left = subprocess.run(["docker", "ps", "-q", "--filter", "name=reprogate-"], stdout=subprocess.PIPE)
        self.assertEqual(left.stdout.strip(), b"")

    def test_missing_image_is_env_failure(self):
        o = evaluate(self.repo, "python", H.verified_claim(), H.write_repro(self.tmp, "good.py", H.GOOD_REPRO),
                     os.path.join(self.tmp, "ev2"), runs=3, timeout=30, min_completed=3,
                     sandbox=sbx.make("reprogate-no-such-image:0"))
        self.assertEqual((o["outcome"], o["outcome_reason"]), (C.NOT_EVALUATED, C.ENVIRONMENT_UNAVAILABLE))


if __name__ == "__main__":
    unittest.main()
