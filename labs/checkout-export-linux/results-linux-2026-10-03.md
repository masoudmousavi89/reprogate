# Linux + Docker results for the checkout export and the writable /work (raw output of run_checkout_export_linux.sh)

Environment: Linux 6.18.44-fc-v51, Python 3.8.20, git version 2.43.0, Docker 29.3.1, base image mirror.gcr.io/library/python:3.8-slim, lab images reprogate-jinja-pinned:export (id sha256:975633a48b7c) and reprogate-jinja-unpinned:export (id sha256:52f20cdd8a5a); user root (uid 0); source clone of pallets/jinja at HEAD 5ef70112.

## (a) F-050 reproducers d1-d4 (+ d0 walk-up probe) against the export checkout, host and Docker mode

```
=== d0 [host] (evaluate gate=False)
real gate on this reproducer: VALID
reproducer stderr last line (run 1): 
reproducer stdout (run 1): d0_walk_up_from_cwd_and_checkout: .git entries found: []
d0_checkout_listing_top: ['minilib']
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json mode TREE_EXPORT_FROM_SHA cleanup REMOVED has_git_entry False files_written 2 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged True | refs before/after 1 1
checkout.json source_head before/after: 066dd1d159c2 066dd1d159c2
git rev-parse HEAD of the source: rc 0 066dd1d159c2361c729a133bc4d00979d12dabd5
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
=== d1 [host] (evaluate gate=False)
real gate on this reproducer: VALID
reproducer stderr last line (run 1): FileNotFoundError: [Errno 2] No such file or directory: '/tmp/reprogate-checkout-c9jhc7y7/repo/.git'
reproducer stdout (run 1): 
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json mode TREE_EXPORT_FROM_SHA cleanup REMOVED has_git_entry False files_written 2 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged True | refs before/after 1 1
checkout.json source_head before/after: cd12b0024203 cd12b0024203
git rev-parse HEAD of the source: rc 0 cd12b0024203064614b521182a99416d406fb25e
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
=== d2 [host] (evaluate gate=False)
real gate on this reproducer: VALID
reproducer stderr last line (run 1): FileNotFoundError: [Errno 2] No such file or directory: '/tmp/reprogate-checkout-qedbdpny/repo/.git'
reproducer stdout (run 1): 
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json mode TREE_EXPORT_FROM_SHA cleanup REMOVED has_git_entry False files_written 2 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged True | refs before/after 1 1
checkout.json source_head before/after: 5766a3007ede 5766a3007ede
git rev-parse HEAD of the source: rc 0 5766a3007edee1bc915e2a818c154e8259dcdfcb
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
=== d3 [host] (evaluate gate=False)
real gate on this reproducer: UNSAFE
reproducer stderr last line (run 1): FileNotFoundError: [Errno 2] No such file or directory: '/tmp/reprogate-checkout-od5e67g8/repo/.git'
reproducer stdout (run 1): 
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json mode TREE_EXPORT_FROM_SHA cleanup REMOVED has_git_entry False files_written 2 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged True | refs before/after 1 1
checkout.json source_head before/after: 59ff5f7859de 59ff5f7859de
git rev-parse HEAD of the source: rc 0 59ff5f7859de1f3a5eb95344ce929f85b852fd07
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
=== d4 [host] (evaluate gate=True)
real gate on this reproducer: VALID
reproducer stderr last line (run 1): FileNotFoundError: [Errno 2] No such file or directory: '/tmp/reprogate-checkout-f2u1026b/repo/.git'
reproducer stdout (run 1): 
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json mode TREE_EXPORT_FROM_SHA cleanup REMOVED has_git_entry False files_written 2 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged True | refs before/after 1 1
checkout.json source_head before/after: 5fc87c34a2b7 5fc87c34a2b7
git rev-parse HEAD of the source: rc 0 5fc87c34a2b7c4dc4577c0bdbe792ee5b6894e7d
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
=== d0 [docker] (evaluate gate=False)
real gate on this reproducer: VALID
reproducer stderr last line (run 1): 
reproducer stdout (run 1): d0_walk_up_from_cwd_and_checkout: .git entries found: []
d0_checkout_listing_top: ['minilib']
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json mode TREE_EXPORT_FROM_SHA cleanup REMOVED has_git_entry False files_written 2 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged True | refs before/after 1 1
checkout.json source_head before/after: 5fc87c34a2b7 5fc87c34a2b7
git rev-parse HEAD of the source: rc 0 5fc87c34a2b7c4dc4577c0bdbe792ee5b6894e7d
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
=== d1 [docker] (evaluate gate=False)
real gate on this reproducer: VALID
reproducer stderr last line (run 1): FileNotFoundError: [Errno 2] No such file or directory: '/repo/.git'
reproducer stdout (run 1): 
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json mode TREE_EXPORT_FROM_SHA cleanup REMOVED has_git_entry False files_written 2 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged True | refs before/after 1 1
checkout.json source_head before/after: aff0084a147b aff0084a147b
git rev-parse HEAD of the source: rc 0 aff0084a147b4272390a5e291d93316152f46f0c
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
=== d2 [docker] (evaluate gate=False)
real gate on this reproducer: VALID
reproducer stderr last line (run 1): FileNotFoundError: [Errno 2] No such file or directory: '/repo/.git'
reproducer stdout (run 1): 
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json mode TREE_EXPORT_FROM_SHA cleanup REMOVED has_git_entry False files_written 2 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged True | refs before/after 1 1
checkout.json source_head before/after: 610c024f618d 610c024f618d
git rev-parse HEAD of the source: rc 0 610c024f618d2feb667e6d1a4b8e02aa46b0be35
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
=== d3 [docker] (evaluate gate=False)
real gate on this reproducer: UNSAFE
reproducer stderr last line (run 1): FileNotFoundError: [Errno 2] No such file or directory: '/repo/.git'
reproducer stdout (run 1): 
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json mode TREE_EXPORT_FROM_SHA cleanup REMOVED has_git_entry False files_written 2 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged True | refs before/after 1 1
checkout.json source_head before/after: 2f1cf97c474f 2f1cf97c474f
git rev-parse HEAD of the source: rc 0 2f1cf97c474f53766000b8423fc510b37e1e01eb
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
=== d4 [docker] (evaluate gate=True)
real gate on this reproducer: VALID
reproducer stderr last line (run 1): FileNotFoundError: [Errno 2] No such file or directory: '/repo/.git'
reproducer stdout (run 1): 
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED']
checkout.json mode TREE_EXPORT_FROM_SHA cleanup REMOVED has_git_entry False files_written 2 | source_head unchanged True
source tree hash unchanged True | whole .git unchanged True | refs before/after 1 1
checkout.json source_head before/after: 91bb898e4808 91bb898e4808
git rev-parse HEAD of the source: rc 0 91bb898e48087ff42727f357b97008291d095b1b
git fsck of the source: rc 0 |  
cat-file -t <fixed commit>: rc 0 commit
later Checkout(source, <fixed commit>): OK
```

## (b) oracle --before-sha/--after-sha in Docker mode; tree hashes against the Windows references

```
export of 81825095 took 0.06 s, files_written 126
export of 9a7dd7b2 took 0.04 s, files_written 126
before: ['SYMPTOM_REPRODUCED', 'NONE'] | after: ['NO_MATCHING_REPRODUCTION_FOUND', 'NONE'] | post-fix: CLEAN_COMPLETION
ORACLE PASS | exit 0
before SYMPTOM_REPRODUCED NONE PROVENANCE_UNVERIFIED counts {'clean_completion_runs': 0, 'completed': 5, 'env_failures': 0, 'invalid': 0, 'matching': 5, 'timeouts': 0, 'total': 5} sandbox DOCKER
  checkout.json {'mode': 'TREE_EXPORT_FROM_SHA', 'requested_sha': '81825095d24f4dbccb40f787fff70db54989b91c', 'head_sha': '81825095d24f4dbccb40f787fff70db54989b91c', 'files_written': 126, 'symlinks_created': 0, 'submodules_not_checked_out': 0, 'blobs_verified': True, 'has_git_entry': False, 'cleanup': 'REMOVED'} source_head_unchanged True
  tree hash dbc9cd7de8574222 equals Windows reference: True | git.commit 81825095 dirty 0
after NO_MATCHING_REPRODUCTION_FOUND NONE PROVENANCE_UNVERIFIED counts {'clean_completion_runs': 5, 'completed': 5, 'env_failures': 0, 'invalid': 0, 'matching': 0, 'timeouts': 0, 'total': 5} sandbox DOCKER
  checkout.json {'mode': 'TREE_EXPORT_FROM_SHA', 'requested_sha': '9a7dd7b28b50fd8adc019ab2702b50ae5c6ed782', 'head_sha': '9a7dd7b28b50fd8adc019ab2702b50ae5c6ed782', 'files_written': 126, 'symlinks_created': 0, 'submodules_not_checked_out': 0, 'blobs_verified': True, 'has_git_entry': False, 'cleanup': 'REMOVED'} source_head_unchanged True
  tree hash bf8ae6f92378232b equals Windows reference: True | git.commit 9a7dd7b2 dirty 0
SOURCE_IDENTICAL True (tree, whole .git, HEAD, refs, worktree count)
```

## (c) /work and the other clauses of req_005, docker inspect saved in docker-inspect-linux.json, compared with labs/checkout-sha-docker/docker-inspect-linux.json

```
containers seen by docker inspect: 4 distinct ids: 4 distinct names: 4
  /reprogate-9fe4a0ab3946 Tmpfs {'/tmp': 'rw,size=64m,noexec,nosuid', '/work': 'rw,size=64m,noexec,nosuid,mode=1777'} | binds [] | all other fields equal a container of the previous inspect (after removing mode=1777 from /work): True
  /reprogate-1bf0f6469bbb Tmpfs {'/tmp': 'rw,size=64m,noexec,nosuid', '/work': 'rw,size=64m,noexec,nosuid,mode=1777'} | binds ['/out:rw', '/repo:ro', '/rg/harness.py:ro', '/rg/repro.py:ro'] | all other fields equal a container of the previous inspect (after removing mode=1777 from /work): True
  /reprogate-b6e56731038d Tmpfs {'/tmp': 'rw,size=64m,noexec,nosuid', '/work': 'rw,size=64m,noexec,nosuid,mode=1777'} | binds ['/out:rw', '/repo:ro', '/rg/harness.py:ro', '/rg/repro.py:ro'] | all other fields equal a container of the previous inspect (after removing mode=1777 from /work): True
  /reprogate-3d5b2a1ef4dd Tmpfs {'/tmp': 'rw,size=64m,noexec,nosuid', '/work': 'rw,size=64m,noexec,nosuid,mode=1777'} | binds ['/out:rw', '/repo:ro', '/rg/harness.py:ro', '/rg/repro.py:ro'] | all other fields equal a container of the previous inspect (after removing mode=1777 from /work): True
one container: {'NetworkMode': 'none', 'ReadonlyRootfs': True, 'CapDrop': ['ALL'], 'SecurityOpt': ['no-new-privileges'], 'PidsLimit': 128, 'Memory': 536870912, 'MemorySwap': 536870912, 'NanoCpus': 1000000000, 'AutoRemove': True, 'Privileged': False} user 65534:65534
outcome NO_MATCHING_REPRODUCTION_FOUND NONE run_status ['COMPLETED', 'COMPLETED', 'COMPLETED'] counts {'total': 3, 'completed': 3, 'env_failures': 0, 'timeouts': 0, 'invalid': 0, 'matching': 0, 'clean_completion_runs': 3}
run 1: uid 65534 NoNewPrivs 1 CapEff 0000000000000000 net ['lo'] connect FAILED ENETUNREACH
   cwd /work | /work mode 0o41777 | /tmp mode 0o41777 | mounts /work ['tmpfs', ['rw', 'nosuid', 'noexec', 'size=65536k']]
   writes {'write_/': 'FAILED EROFS', 'write_/out/probe-out': 'WROTE', 'write_/repo/x': 'FAILED EROFS', 'write_/tmp/marker': 'WROTE', 'write_/work/marker': 'WROTE', 'write_cwd/marker_cwd': 'WROTE'}
   markers present at start: /tmp False /work False | canary visible False
   cgroup limits {'cpu_cpu.cfs_period_us': '100000', 'cpu_cpu.cfs_quota_us': '100000', 'memory_memory.limit_in_bytes': '536870912', 'memory_memory.memsw.limit_in_bytes': '536870912', 'pids_pids.max': '128'}
run 2: uid 65534 NoNewPrivs 1 CapEff 0000000000000000 net ['lo'] connect FAILED ENETUNREACH
   cwd /work | /work mode 0o41777 | /tmp mode 0o41777 | mounts /work ['tmpfs', ['rw', 'nosuid', 'noexec', 'size=65536k']]
   writes {'write_/': 'FAILED EROFS', 'write_/out/probe-out': 'WROTE', 'write_/repo/x': 'FAILED EROFS', 'write_/tmp/marker': 'WROTE', 'write_/work/marker': 'WROTE', 'write_cwd/marker_cwd': 'WROTE'}
   markers present at start: /tmp False /work False | canary visible False
   cgroup limits {'cpu_cpu.cfs_period_us': '100000', 'cpu_cpu.cfs_quota_us': '100000', 'memory_memory.limit_in_bytes': '536870912', 'memory_memory.memsw.limit_in_bytes': '536870912', 'pids_pids.max': '128'}
run 3: uid 65534 NoNewPrivs 1 CapEff 0000000000000000 net ['lo'] connect FAILED ENETUNREACH
   cwd /work | /work mode 0o41777 | /tmp mode 0o41777 | mounts /work ['tmpfs', ['rw', 'nosuid', 'noexec', 'size=65536k']]
   writes {'write_/': 'FAILED EROFS', 'write_/out/probe-out': 'WROTE', 'write_/repo/x': 'FAILED EROFS', 'write_/tmp/marker': 'WROTE', 'write_/work/marker': 'WROTE', 'write_cwd/marker_cwd': 'WROTE'}
   markers present at start: /tmp False /work False | canary visible False
   cgroup limits {'cpu_cpu.cfs_period_us': '100000', 'cpu_cpu.cfs_quota_us': '100000', 'memory_memory.limit_in_bytes': '536870912', 'memory_memory.memsw.limit_in_bytes': '536870912', 'pids_pids.max': '128'}
env names inside: ['GPG_KEY', 'HOME', 'HOSTNAME', 'LANG', 'PATH', 'PYTHONDONTWRITEBYTECODE', 'PYTHONHASHSEED', 'PYTHONIOENCODING', 'PYTHONNOUSERSITE', 'PYTHON_VERSION']
inside but not in env_names(): ['GPG_KEY', 'HOME', 'HOSTNAME', 'PYTHON_VERSION']
containers left after the run: 0
```

## (d) POSIX export: exec bit, symlinks, case-only names (throwaway repository)

```
tracked modes: {'run.sh': '100755', 'plain.txt': '100644', 'link': '120000', 'filelink': '120000', 'A.txt': '100644', 'a.txt': '100644'}
export took 0.01 s
exec bit run.sh: True | exec bit plain.txt: False
link is symlink: True target text: ../..
filelink is symlink: True target text: plain.txt
A.txt: upper | a.txt: lower | listing has both: True
tree_hash of the checkout finished in 0.00 s (does not recurse through link): 513cece418dad14a, files hashed 7
.git anywhere in checkout: []
record: {'mode': 'TREE_EXPORT_FROM_SHA', 'files_written': 6, 'symlinks_created': 2, 'submodules_not_checked_out': 0, 'has_git_entry': False, 'cleanup': 'REMOVED'}
through the tool: outcome NO_MATCHING_REPRODUCTION_FOUND NONE ['COMPLETED', 'COMPLETED', 'COMPLETED'] | checkout.json {'files_written': 6, 'symlinks_created': 2, 'cleanup': 'REMOVED', 'has_git_entry': False}
reproducer stdout: seen_by_reproducer ['A.txt', 'a.txt', 'filelink', 'link', 'minilib', 'plain.txt', 'run.sh'] | link_is_symlink True ../.. | exec_bit_run_sh True
SOURCE_IDENTICAL True
```

## (e) jinja-843 through --checkout-sha, Docker mode (six rows)

```
before: ['SYMPTOM_REPRODUCED', 'NONE'] | after: ['NO_MATCHING_REPRODUCTION_FOUND', 'NONE'] | post-fix: CLEAN_COMPLETION
ORACLE PASS
outcome: NOT_EVALUATED | reason: ENVIRONMENT_UNAVAILABLE | qualifier: PROVENANCE_UNVERIFIED
runs: ['ENV_FAILURE', 'ENV_FAILURE', 'ENV_FAILURE', 'ENV_FAILURE', 'ENV_FAILURE'] | counts: {'total': 5, 'completed': 0, 'env_failures': 5, 'timeouts': 0, 'invalid': 0, 'matching': 0, 'clean_completion_runs': 0}
evidence: <HOME>/coexp-work/ev-jinja/case_c_unpinned
outcome: NOT_EVALUATED | reason: REPRODUCER_REJECTED | qualifier: PROVENANCE_UNVERIFIED
runs: [] | counts: {'total': 0, 'completed': 0, 'env_failures': 0, 'timeouts': 0, 'invalid': 0, 'matching': 0, 'clean_completion_runs': 0}
evidence: <HOME>/coexp-work/ev-jinja/f01_direct_raise
outcome: NO_MATCHING_REPRODUCTION_FOUND | reason: NONE | qualifier: PROVENANCE_UNVERIFIED
runs: ['COMPLETED', 'COMPLETED', 'COMPLETED', 'COMPLETED', 'COMPLETED'] | counts: {'total': 5, 'completed': 5, 'env_failures': 0, 'timeouts': 0, 'invalid': 0, 'matching': 0, 'clean_completion_runs': 0}
evidence: <HOME>/coexp-work/ev-jinja/f02_direct_deque_popleft
outcome: NO_MATCHING_REPRODUCTION_FOUND | reason: NONE | qualifier: PROVENANCE_UNVERIFIED
runs: ['COMPLETED', 'COMPLETED', 'COMPLETED', 'COMPLETED', 'COMPLETED'] | counts: {'total': 5, 'completed': 5, 'env_failures': 0, 'timeouts': 0, 'invalid': 0, 'matching': 0, 'clean_completion_runs': 5}
evidence: <HOME>/coexp-work/ev-jinja/f03_fake_traceback_stdout
outcome: NO_MATCHING_REPRODUCTION_FOUND | reason: NONE | qualifier: PROVENANCE_UNVERIFIED
runs: ['COMPLETED', 'COMPLETED', 'COMPLETED', 'COMPLETED', 'COMPLETED'] | counts: {'total': 5, 'completed': 5, 'env_failures': 0, 'timeouts': 0, 'invalid': 0, 'matching': 0, 'clean_completion_runs': 0}
evidence: <HOME>/coexp-work/ev-jinja/f04_subclass_override
| case | expected | actual | ok |
|---|---|---|---|
| oracle | before=['SYMPTOM_REPRODUCED', 'NONE'] post=CLEAN_COMPLETION pass=True | before=['SYMPTOM_REPRODUCED', 'NONE'] post=CLEAN_COMPLETION pass=True | YES |
| case_c_unpinned | NOT_EVALUATED/ENVIRONMENT_UNAVAILABLE | NOT_EVALUATED/ENVIRONMENT_UNAVAILABLE | YES |
| f01_direct_raise | NOT_EVALUATED/REPRODUCER_REJECTED | NOT_EVALUATED/REPRODUCER_REJECTED | YES |
| f02_direct_deque_popleft | NO_MATCHING_REPRODUCTION_FOUND/NONE | NO_MATCHING_REPRODUCTION_FOUND/NONE | YES |
| f03_fake_traceback_stdout | NO_MATCHING_REPRODUCTION_FOUND/NONE | NO_MATCHING_REPRODUCTION_FOUND/NONE | YES |
| f04_subclass_override | NO_MATCHING_REPRODUCTION_FOUND/NONE | NO_MATCHING_REPRODUCTION_FOUND/NONE | YES |

```

## (e, static) file-writing calls in reproducers and fixtures under labs/

```
reproducer/fixture files scanned: 83 | lab reproducers and fixtures: 43 | deliberate attack or probe files: 40
lab reproducers/fixtures with file-writing calls: none
deliberate attack/probe files with file-writing calls: 13 of 40
```
