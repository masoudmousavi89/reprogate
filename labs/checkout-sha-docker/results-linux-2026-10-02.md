# Linux + Docker results for the checkout-by-SHA change (raw output of run_checkout_docker.sh)

Environment: Linux 6.18.44-fc-v51, Python 3.8.20, git version 2.43.0, Docker 29.3.1, base image mirror.gcr.io/library/python:3.8-slim, lab image reprogate-jinja-pinned:cosha (image id sha256:0a2de8a5a3cb); user root (uid 0); source clone of pallets/jinja at HEAD 5ef70112.

## (a) oracle --before-sha/--after-sha in Docker mode

```
before: ['SYMPTOM_REPRODUCED', 'NONE'] | after: ['NO_MATCHING_REPRODUCTION_FOUND', 'NONE'] | post-fix: CLEAN_COMPLETION
ORACLE PASS
oracle exit code 0
before SYMPTOM_REPRODUCED NONE PROVENANCE_UNVERIFIED counts {'clean_completion_runs': 0, 'completed': 5, 'env_failures': 0, 'invalid': 0, 'matching': 5, 'timeouts': 0, 'total': 5} sandbox DOCKER
  checkout.json {'requested_sha': '81825095d24f4dbccb40f787fff70db54989b91c', 'head_sha': '81825095d24f4dbccb40f787fff70db54989b91c', 'cleanup': 'REMOVED', 'source_worktrees_before': 1, 'source_worktrees_after': 1} source_head_unchanged True
  environment git.commit 81825095d24f4dbccb40f787fff70db54989b91c tree dbc9cd7de8574222
after NO_MATCHING_REPRODUCTION_FOUND NONE PROVENANCE_UNVERIFIED counts {'clean_completion_runs': 5, 'completed': 5, 'env_failures': 0, 'invalid': 0, 'matching': 0, 'timeouts': 0, 'total': 5} sandbox DOCKER
  checkout.json {'requested_sha': '9a7dd7b28b50fd8adc019ab2702b50ae5c6ed782', 'head_sha': '9a7dd7b28b50fd8adc019ab2702b50ae5c6ed782', 'cleanup': 'REMOVED', 'source_worktrees_before': 1, 'source_worktrees_after': 1} source_head_unchanged True
  environment git.commit 9a7dd7b28b50fd8adc019ab2702b50ae5c6ed782 tree bf8ae6f92378232b
source before {'head': '5ef70112a1ff19c05324ff889dd30405b1002044', 'worktrees': 1, 'tree_sha256': '4ef4ddf1ff2de6383f1593f810daf0c66c5df73597d68a8402d6afa7ff913c0e', 'git_dir_sha256': '260b3bd86ea9b18c83f5b75c396aa0d51ddb0ee927d41a4f64d75b431d8eb258', 'refs': 62}
source after  {'head': '5ef70112a1ff19c05324ff889dd30405b1002044', 'worktrees': 1, 'tree_sha256': '4ef4ddf1ff2de6383f1593f810daf0c66c5df73597d68a8402d6afa7ff913c0e', 'git_dir_sha256': '260b3bd86ea9b18c83f5b75c396aa0d51ddb0ee927d41a4f64d75b431d8eb258', 'refs': 62}
SOURCE_IDENTICAL True
```

## (b) what the container sees

```
docker run rc 0
{
 "git_binary": null,
 "dot_git_is_file": true,
 "dot_git_content": "gitdir: <HOME>/cosha-work/jinja/.git/worktrees/repo",
 "gitdir_exists_in_container": false,
 "write_tracked_file": "FAILED EACCES",
 "write_dot_git": "FAILED EACCES",
 "create_in_repo": "FAILED EROFS",
 "write_host_gitdir_HEAD": "FAILED EACCES",
 "create_host_path": "FAILED EACCES",
 "create_in_root": "FAILED EROFS",
 "mount_options_repo": [
  "ro,relatime,discard,resv_strict,resuid=65534,resgid=65534"
 ]
}


git -C /repo status in the container: rc 128 fatal: not a git repository: (null)
finish: REMOVED
```

## (c) write attempts through the real tool (real gate), Docker mode

```
outcome: NO_MATCHING_REPRODUCTION_FOUND | reason: NONE | qualifier: PROVENANCE_UNVERIFIED
runs: ['COMPLETED', 'COMPLETED', 'COMPLETED', 'COMPLETED', 'COMPLETED'] | counts: {'total': 5, 'completed': 5, 'env_failures': 0, 'timeouts': 0, 'invalid': 0, 'matching': 0, 'clean_completion_runs': 5}
evidence: <HOME>/cosha-work/out-c | exit 0
outcome NO_MATCHING_REPRODUCTION_FOUND NONE gate VALID counts {'clean_completion_runs': 5, 'completed': 5, 'env_failures': 0, 'invalid': 0, 'matching': 0, 'timeouts': 0, 'total': 5}
tracked_file FAILED EACCES /repo/jinja2/utils.py
dot_git FAILED EACCES /repo/.git
gitdir_named_in_dot_git <HOME>/cosha-work/jinja/.git/worktrees/repo exists False
host_gitdir_HEAD FAILED EACCES <HOME>/cosha-work/jinja/.git/worktrees/repo/HEAD
host_gitdir_new FAILED EACCES <HOME>/cosha-work/jinja/.git/worktrees/repo/pwned
host_common_refs FAILED EACCES <HOME>/cosha-work/jinja/.git/worktrees/repo/../../refs/heads/pwned
root_fs FAILED EROFS /pwned

checkout.json cleanup REMOVED worktrees 1 -> 1
SOURCE_IDENTICAL True (tree, whole .git, HEAD, refs, worktree count)
```

## (d) and (d-docker) reachability of the source .git from a worktree (throwaway repository)

```
=== d1 [host] (evaluate gate=False)
real gate on this reproducer: VALID
reproducer stdout (run 1): gitdir <SRC>/.git/worktrees/repo exists True
d1_append_to_worktree_metadata_HEAD WROTE <SRC>/.git/worktrees/repo/HEAD
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json cleanup REMOVED worktrees 1 -> 1 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged True | refs before/after 1 1
checkout.json source_head before/after: 52300eae2f29 52300eae2f29
git rev-parse HEAD of the source: rc 0 52300eae2f298a64c012d4bff9af276d0a783007
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
=== d2 [host] (evaluate gate=False)
real gate on this reproducer: VALID
reproducer stdout (run 1): gitdir <SRC>/.git/worktrees/repo exists True
d2_create_ref_in_source_git WROTE <SRC>/.git/refs/heads/pwned
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json cleanup REMOVED worktrees 1 -> 1 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged False | refs before/after 1 2
  new refs: ['refs/heads/pwned a8c733d509a193fd546326c232801e7505f4ea85']
checkout.json source_head before/after: ce830c693dd8 ce830c693dd8
git rev-parse HEAD of the source: rc 0 ce830c693dd8d04621274150de91703513ef61e3
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
=== d3 [host] (evaluate gate=False)
real gate on this reproducer: UNSAFE
reproducer stdout (run 1): gitdir <SRC>/.git/worktrees/repo exists True
d3_unlink_loose_object WROTE <SRC>/.git/objects/0f/ab0305020ae1ba666099067097464667ab19d0
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json cleanup REMOVED worktrees 1 -> 1 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged False | refs before/after 1 1
checkout.json source_head before/after: 0fab0305020a 0fab0305020a
git rev-parse HEAD of the source: rc 0 0fab0305020ae1ba666099067097464667ab19d0
git fsck of the source: rc 2 |  error: refs/heads/master: invalid sha1 pointer 0fab0305020ae1ba666099067097464667ab19d0 ; error: HEAD: invalid sha1 pointer 0fab0305020ae1ba666099067097464667ab19d0 ; error: refs/heads/master: invalid reflog entry 0fab0305020ae1ba666099067097464667ab19d0 ; error: HEAD: invalid reflog entry 0fab0305020ae1
cat-file -t <fixed commit>: rc 128 fatal: git cat-file: could not get object info
later Checkout(source, <fixed commit>): ValueError: commit 0fab0305020ae1ba666099067097464667ab19d0 not found in <TMP>/src: fatal: git cat-file: could not get object info
=== d4 [host] (evaluate gate=True)
real gate on this reproducer: VALID
reproducer stdout (run 1): gitdir <SRC>/.git/worktrees/repo exists True
d4_overwrite_branch_ref_in_source_git WROTE <SRC>/.git/refs/heads/master
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json cleanup REMOVED worktrees 1 -> 1 | source_head unchanged False
source tree hash unchanged True | whole .git unchanged False | refs before/after 1 1
  new refs: ['refs/heads/master 1111111111111111111111111111111111111111']
checkout.json source_head before/after: 4ce61ceaa39d 111111111111
git rev-parse HEAD of the source: rc 0 1111111111111111111111111111111111111111
git fsck of the source: rc 2 |  error: refs/heads/master: invalid sha1 pointer 1111111111111111111111111111111111111111 ; error: HEAD: invalid sha1 pointer 1111111111111111111111111111111111111111 ; notice: No default references
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
=== d1 [docker] (evaluate gate=False)
real gate on this reproducer: VALID
reproducer stdout (run 1): gitdir <SRC>/.git/worktrees/repo exists False
d1_append_to_worktree_metadata_HEAD FAILED 2 <SRC>/.git/worktrees/repo/HEAD
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json cleanup REMOVED worktrees 1 -> 1 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged True | refs before/after 1 1
checkout.json source_head before/after: 7e471037826a 7e471037826a
git rev-parse HEAD of the source: rc 0 7e471037826a1b49d230a703a9b45ea58a628e13
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
=== d2 [docker] (evaluate gate=False)
real gate on this reproducer: VALID
reproducer stdout (run 1): gitdir <SRC>/.git/worktrees/repo exists False
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json cleanup REMOVED worktrees 1 -> 1 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged True | refs before/after 1 1
checkout.json source_head before/after: 3a2c4d86fa39 3a2c4d86fa39
git rev-parse HEAD of the source: rc 0 3a2c4d86fa3987122a130206c05e919dd273c1f6
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
=== d3 [docker] (evaluate gate=False)
real gate on this reproducer: UNSAFE
reproducer stdout (run 1): gitdir <SRC>/.git/worktrees/repo exists False
d3_unlink_loose_object FAILED 2 <SRC>/.git/objects/88/5c8286d9cc5744a46d9a70d0c04d5a07c4bbbf
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json cleanup REMOVED worktrees 1 -> 1 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged True | refs before/after 1 1
checkout.json source_head before/after: 885c8286d9cc 885c8286d9cc
git rev-parse HEAD of the source: rc 0 885c8286d9cc5744a46d9a70d0c04d5a07c4bbbf
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
=== d4 [docker] (evaluate gate=True)
real gate on this reproducer: VALID
reproducer stdout (run 1): gitdir <SRC>/.git/worktrees/repo exists False
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json cleanup REMOVED worktrees 1 -> 1 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged True | refs before/after 1 1
checkout.json source_head before/after: d1690150a0ef d1690150a0ef
git rev-parse HEAD of the source: rc 0 d1690150a0ef527f287cd6d0cdcef83c1752b8e4
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
```

## (e) req_005 clauses, Docker mode, docker inspect saved in docker-inspect-linux.json

```
containers seen by docker inspect: 4 distinct ids: 4 distinct names: 4
  /reprogate-ef14e2a40d61 network none ro_root True CapDrop ['ALL'] CapAdd None secopt ['no-new-privileges'] user 65534:65534 mem 536870912 swap 536870912 nanocpus 1000000000 pids 128 autoremove True privileged False
    tmpfs {'/tmp': 'rw,size=64m,noexec,nosuid', '/work': 'rw,size=64m,noexec,nosuid'} | binds []
  /reprogate-08f021b1fb9c network none ro_root True CapDrop ['ALL'] CapAdd None secopt ['no-new-privileges'] user 65534:65534 mem 536870912 swap 536870912 nanocpus 1000000000 pids 128 autoremove True privileged False
    tmpfs {'/tmp': 'rw,size=64m,noexec,nosuid', '/work': 'rw,size=64m,noexec,nosuid'} | binds ['/rg/harness.py:ro', '/rg/repro.py:ro', '/out:rw', '/repo:ro']
  /reprogate-e992d3333674 network none ro_root True CapDrop ['ALL'] CapAdd None secopt ['no-new-privileges'] user 65534:65534 mem 536870912 swap 536870912 nanocpus 1000000000 pids 128 autoremove True privileged False
    tmpfs {'/tmp': 'rw,size=64m,noexec,nosuid', '/work': 'rw,size=64m,noexec,nosuid'} | binds ['/repo:ro', '/rg/harness.py:ro', '/rg/repro.py:ro', '/out:rw']
  /reprogate-811c27eb0a5c network none ro_root True CapDrop ['ALL'] CapAdd None secopt ['no-new-privileges'] user 65534:65534 mem 536870912 swap 536870912 nanocpus 1000000000 pids 128 autoremove True privileged False
    tmpfs {'/tmp': 'rw,size=64m,noexec,nosuid', '/work': 'rw,size=64m,noexec,nosuid'} | binds ['/repo:ro', '/rg/harness.py:ro', '/rg/repro.py:ro', '/out:rw']
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED'] counts {'total': 3, 'completed': 3, 'env_failures': 0, 'timeouts': 0, 'invalid': 0, 'matching': 0, 'clean_completion_runs': 3}
run 1: uid 65534 gid 65534 NoNewPrivs 1 CapEff 0000000000000000 CapBnd 0000000000000000 net ['lo'] connect FAILED ENETUNREACH hostname 1ab3dbca3771
   cgroup {'cgroup_cpu.max': 'unreadable ENOENT', 'cgroup_cpu_cpu.cfs_period_us': '100000', 'cgroup_cpu_cpu.cfs_quota_us': '100000', 'cgroup_memory.max': 'unreadable ENOENT', 'cgroup_memory.swap.max': 'unreadable ENOENT', 'cgroup_memory_memory.limit_in_bytes': '536870912', 'cgroup_memory_memory.memsw.limit_in_bytes': '536870912', 'cgroup_pids.max': 'unreadable ENOENT', 'cgroup_pids_pids.max': '128'}
   mounts {'/': ['overlay', ['ro']], '/out': ['ext4', ['rw']], '/repo': ['ext4', ['ro']], '/rg/harness.py': ['ext4', ['ro']], '/rg/repro.py': ['ext4', ['ro']], '/tmp': ['tmpfs', ['rw', 'nosuid', 'noexec', 'size=65536k']], '/work': ['tmpfs', ['rw', 'nosuid', 'noexec', 'size=65536k']]}
   writes {'write_/': 'FAILED EROFS', 'write_/out/probe-out': 'WROTE', 'write_/repo/x': 'FAILED EROFS', 'write_/tmp/marker': 'WROTE', 'write_/work/marker': 'FAILED EACCES'} | markers present at start: tmp False work False | canary visible False
run 2: uid 65534 gid 65534 NoNewPrivs 1 CapEff 0000000000000000 CapBnd 0000000000000000 net ['lo'] connect FAILED ENETUNREACH hostname c352d42f48d4
   cgroup {'cgroup_cpu.max': 'unreadable ENOENT', 'cgroup_cpu_cpu.cfs_period_us': '100000', 'cgroup_cpu_cpu.cfs_quota_us': '100000', 'cgroup_memory.max': 'unreadable ENOENT', 'cgroup_memory.swap.max': 'unreadable ENOENT', 'cgroup_memory_memory.limit_in_bytes': '536870912', 'cgroup_memory_memory.memsw.limit_in_bytes': '536870912', 'cgroup_pids.max': 'unreadable ENOENT', 'cgroup_pids_pids.max': '128'}
   mounts {'/': ['overlay', ['ro']], '/out': ['ext4', ['rw']], '/repo': ['ext4', ['ro']], '/rg/harness.py': ['ext4', ['ro']], '/rg/repro.py': ['ext4', ['ro']], '/tmp': ['tmpfs', ['rw', 'nosuid', 'noexec', 'size=65536k']], '/work': ['tmpfs', ['rw', 'nosuid', 'noexec', 'size=65536k']]}
   writes {'write_/': 'FAILED EROFS', 'write_/out/probe-out': 'WROTE', 'write_/repo/x': 'FAILED EROFS', 'write_/tmp/marker': 'WROTE', 'write_/work/marker': 'FAILED EACCES'} | markers present at start: tmp False work False | canary visible False
run 3: uid 65534 gid 65534 NoNewPrivs 1 CapEff 0000000000000000 CapBnd 0000000000000000 net ['lo'] connect FAILED ENETUNREACH hostname 240d79c150eb
   cgroup {'cgroup_cpu.max': 'unreadable ENOENT', 'cgroup_cpu_cpu.cfs_period_us': '100000', 'cgroup_cpu_cpu.cfs_quota_us': '100000', 'cgroup_memory.max': 'unreadable ENOENT', 'cgroup_memory.swap.max': 'unreadable ENOENT', 'cgroup_memory_memory.limit_in_bytes': '536870912', 'cgroup_memory_memory.memsw.limit_in_bytes': '536870912', 'cgroup_pids.max': 'unreadable ENOENT', 'cgroup_pids_pids.max': '128'}
   mounts {'/': ['overlay', ['ro']], '/out': ['ext4', ['rw']], '/repo': ['ext4', ['ro']], '/rg/harness.py': ['ext4', ['ro']], '/rg/repro.py': ['ext4', ['ro']], '/tmp': ['tmpfs', ['rw', 'nosuid', 'noexec', 'size=65536k']], '/work': ['tmpfs', ['rw', 'nosuid', 'noexec', 'size=65536k']]}
   writes {'write_/': 'FAILED EROFS', 'write_/out/probe-out': 'WROTE', 'write_/repo/x': 'FAILED EROFS', 'write_/tmp/marker': 'WROTE', 'write_/work/marker': 'FAILED EACCES'} | markers present at start: tmp False work False | canary visible False
env names inside the container: ['GPG_KEY', 'HOME', 'HOSTNAME', 'LANG', 'PATH', 'PYTHONDONTWRITEBYTECODE', 'PYTHONHASHSEED', 'PYTHONIOENCODING', 'PYTHONNOUSERSITE', 'PYTHON_VERSION']
env_names() of runner.py: ['COMSPEC', 'LANG', 'LC_ALL', 'PATH', 'PATHEXT', 'PYTHONDONTWRITEBYTECODE', 'PYTHONHASHSEED', 'PYTHONIOENCODING', 'PYTHONNOUSERSITE', 'SYSTEMDRIVE', 'SYSTEMROOT', 'TEMP', 'TMP']
inside but not in env_names(): ['GPG_KEY', 'HOME', 'HOSTNAME', 'PYTHON_VERSION']
env_names() not inside: ['COMSPEC', 'LC_ALL', 'PATHEXT', 'SYSTEMDRIVE', 'SYSTEMROOT', 'TEMP', 'TMP']
tree hash before: dbc9cd7de8574222 | outcome repository keys: {'tree_sha256_before': 'dbc9cd7de8574222da889f9f94b65d4fd5054e50f4a09128da7b90f10d983b06'}
containers left after the run: 0
```

## (f) worktree vs git archive

```
81825095 files worktree 126 archive 126 | differences 0 [] | tree_hash equal True dbc9cd7de8574222
  diff -r -q (excluding .git) exit code 0
9a7dd7b2 files worktree 126 archive 126 | differences 0 [] | tree_hash equal True bf8ae6f92378232b
  diff -r -q (excluding .git) exit code 0
```

## (f2) hand-made Lab #1 checkouts, if present (compare with the hashes of (f))

```
jinja-before dbc9cd7de8574222
jinja-after bf8ae6f92378232b
```
