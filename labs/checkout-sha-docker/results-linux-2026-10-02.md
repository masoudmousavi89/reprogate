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
source before {'head': '5ef70112a1ff19c05324ff889dd30405b1002044', 'worktrees': 1, 'tree_sha256': '4ef4ddf1ff2de6383f1593f810daf0c66c5df73597d68a8402d6afa7ff913c0e', 'git_dir_sha256': '54cb2c723555f30cd80cad55c4e29d36f446833dcb6697697a0da909c7ef2b7e', 'refs': 62}
source after  {'head': '5ef70112a1ff19c05324ff889dd30405b1002044', 'worktrees': 1, 'tree_sha256': '4ef4ddf1ff2de6383f1593f810daf0c66c5df73597d68a8402d6afa7ff913c0e', 'git_dir_sha256': '54cb2c723555f30cd80cad55c4e29d36f446833dcb6697697a0da909c7ef2b7e', 'refs': 62}
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
=== d1 [host]
real gate on this reproducer: VALID
reproducer stdout (run 1): gitdir <SRC>/.git/worktrees/repo exists True
d1_append_to_worktree_metadata_HEAD WROTE <SRC>/.git/worktrees/repo/HEAD
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json cleanup REMOVED worktrees 1 -> 1 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged True | refs before/after 1 1
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
=== d2 [host]
real gate on this reproducer: VALID
reproducer stdout (run 1): gitdir <SRC>/.git/worktrees/repo exists True
d2_create_ref_in_source_git WROTE <SRC>/.git/refs/heads/pwned
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json cleanup REMOVED worktrees 1 -> 1 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged False | refs before/after 1 2
  new refs: ['refs/heads/pwned 272a64e37756893ddc587fc4eb953036f5869e48']
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
=== d3 [host]
real gate on this reproducer: UNSAFE
reproducer stdout (run 1): gitdir <SRC>/.git/worktrees/repo exists True
d3_unlink_loose_object WROTE <SRC>/.git/objects/ef/4528072e81f0a93eb1d033e158920ec02e9de9
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json cleanup REMOVED worktrees 1 -> 1 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged False | refs before/after 1 1
git fsck of the source: rc 2 |  error: refs/heads/master: invalid sha1 pointer ef4528072e81f0a93eb1d033e158920ec02e9de9 ; error: HEAD: invalid sha1 pointer ef4528072e81f0a93eb1d033e158920ec02e9de9 ; error: refs/heads/master: invalid reflog entry ef4528072e81f0a93eb1d033e158920ec02e9de9 ; error: HEAD: invalid reflog entry ef4528072e81f0
cat-file -t <fixed commit>: rc 128 fatal: git cat-file: could not get object info
later Checkout(source, <fixed commit>): ValueError: commit ef4528072e81f0a93eb1d033e158920ec02e9de9 not found in <TMP>/src: fatal: git cat-file: could not get object info
=== d1 [docker]
real gate on this reproducer: VALID
reproducer stdout (run 1): gitdir <SRC>/.git/worktrees/repo exists False
d1_append_to_worktree_metadata_HEAD FAILED 2 <SRC>/.git/worktrees/repo/HEAD
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json cleanup REMOVED worktrees 1 -> 1 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged True | refs before/after 1 1
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
=== d2 [docker]
real gate on this reproducer: VALID
reproducer stdout (run 1): gitdir <SRC>/.git/worktrees/repo exists False
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json cleanup REMOVED worktrees 1 -> 1 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged True | refs before/after 1 1
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
=== d3 [docker]
real gate on this reproducer: UNSAFE
reproducer stdout (run 1): gitdir <SRC>/.git/worktrees/repo exists False
d3_unlink_loose_object FAILED 2 <SRC>/.git/objects/27/43b7974db8b3b27ab8beacc027ff2e7b6377a1
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json cleanup REMOVED worktrees 1 -> 1 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged True | refs before/after 1 1
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
```

## (e) req_005 clauses, Docker mode, docker inspect saved in docker-inspect-linux.json

```
containers seen by docker inspect: 4 distinct ids: 4 distinct names: 4
  /reprogate-39e0b419c433 network none ro_root True CapDrop ['ALL'] CapAdd None secopt ['no-new-privileges'] user 65534:65534 mem 536870912 swap 536870912 nanocpus 1000000000 pids 128 autoremove True privileged False
Traceback (most recent call last):
  File "/home/user/reprogate/labs/checkout-sha-docker/step_e.py", line 61, in <module>
    print("    tmpfs", h["Tmpfs"], "| binds", [mask(b).split("/")[-1] if False else re.sub(r"^.*?:/", "/", b) for b in h["Binds"]])
TypeError: 'NoneType' object is not iterable
```

## (f) worktree vs git archive

```
81825095 files worktree 127 archive 126 | differences 1 ['.git'] | tree_hash equal True dbc9cd7de8574222
  diff -r -q (excluding .git) exit code 0
9a7dd7b2 files worktree 127 archive 126 | differences 1 ['.git'] | tree_hash equal True bf8ae6f92378232b
  diff -r -q (excluding .git) exit code 0
```
