# Pilot candidates: every candidate examined, in selection order

Selection as fixed in `PROTOCOL.md` (commit 435b219, before this search): packages of `labs/sample-v3/narrow-packages.json`
in ascending `rank`, minus the excluded repositories (84 repositories); per package the oldest closed issue whose body
contains `expected` and (`actual` or `got`); stop at 5 evaluable or 30 candidates examined. Search run 2026-10-01 through
the unauthenticated GitHub search API.

Result: **30 candidates examined, 0 evaluable.** The sample was not extended and the method was not changed after seeing
this result.

How each row was judged: by reading the issue text (the first 500-1100 characters, and for the closest cases the whole
text and the fix pull request), before any run. Rows marked `title only` were judged from the title alone and not read;
they may deserve a second look. The reading of "can be written as Python literals" is the maintainer's reading and can be
disputed row by row.

| rank | project | issue | verdict | reason |
|---|---|---|---|---|
| 1 | boto/boto3 | #166 | NOT_EVALUATED, cond. 3 | needs an AWS account (network service); also no literal values and no linked fix |
| 2 | pypa/packaging | #371 | NOT_EVALUATED, cond. 1 | an exception inside pip's resolver, no expected/actual values |
| 3 | python/typing_extensions | #126 | NOT_EVALUATED, cond. 1 | an exception (TypeError) |
| 4 | certifi/python-certifi | #203 | NOT_EVALUATED, cond. 1 | an exception under a third-party importer |
| 6 | urllib3/urllib3 | #423 | NOT_EVALUATED, cond. 3 | a timeout against a real remote host (network) |
| 7 | psf/requests | #126 | NOT_EVALUATED, cond. 3 | needs a web server with basic authentication |
| 8 | jawah/charset_normalizer | #136 | NOT_EVALUATED, cond. 1 | an exception; the reproducer needs a 9.6 MB file that is not attached |
| 9 | pypa/setuptools | #19 | NOT_EVALUATED, cond. 1 | a report of failing tests under Python 2.5 |
| 13 | pygments/pygments | #294 | NOT_EVALUATED, cond. 1 | wrong highlighting of a token stream, not a stated expected/actual value |
| 15 | boto/botocore | #395 | NOT_EVALUATED, cond. 1 | an exception (TypeError) triggered by a config file |
| 18 | pydantic/pydantic | #436 | NOT_EVALUATED, cond. 2 | literals exist (`404` becomes `'404'`) but no fix pull request is linked in the issue timeline |
| 21 | eliben/pycparser | #588 | NOT_EVALUATED, cond. 1 | not a bug report (a question about an unmaintained dependency) |
| 22 | agronholm/anyio | #458 | NOT_EVALUATED, cond. 1 | behaviour on Ctrl+C, no values |
| 23 | pytest-dev/pytest | #86 | NOT_EVALUATED, cond. 1 | output capture, no values |
| 26 | aio-libs/aiobotocore | #548 | NOT_EVALUATED, cond. 3 | title only: SSL connection errors (network) |
| 29 | python-attrs/attrs | #5 | NOT_EVALUATED, cond. 1 | an exception (TypeError) |
| 32 | fsspec/filesystem_spec | #295 | NOT_EVALUATED, cond. 1 | title only: a compatibility request, not a wrong value |
| 33 | encode/httpx | #152 | NOT_EVALUATED, cond. 1 | an exception (AttributeError) |
| 35 | encode/httpcore | #110 | NOT_EVALUATED, cond. 3 | title only: sockets in CLOSE_WAIT (network) |
| 37 | theskumar/python-dotenv | #24 | NOT_EVALUATED, cond. 1 | depends on the directory walk of the installed location, no values |
| 38 | tox-dev/platformdirs | #207 | NOT_EVALUATED, cond. 1 | a FileNotFoundError after a directory was not created, no returned value |
| 44 | pypa/pip | #44 | NOT_EVALUATED, cond. 3 | `pip search` against the package index (network) |
| 45 | jpadilla/pyjwt | #168 | NOT_EVALUATED, cond. 1 | an exception (signature verification failed), no values |
| 46 | Kludex/starlette | #289 | NOT_EVALUATED, cond. 1 | closest case: a merged fix with a regression test (PR #291), but the "actual" is a missing header (KeyError), not a wrong value |
| 47 | Kludex/uvicorn | #104 | NOT_EVALUATED, cond. 1 | title only: a NameError under PyPy |
| 50 | tqdm/tqdm | #317 | NOT_EVALUATED, cond. 1 | terminal display timing, no returned value |
| 51 | jmespath/jmespath.py | #139 | NOT_EVALUATED, cond. 1 | an exception |
| 53 | aio-libs/yarl | #25 | NOT_EVALUATED, cond. 1 | an exception (TypeError) |
| 55 | Textualize/rich | #315 | NOT_EVALUATED, cond. 1 | title only: a feature request |
| 56 | executablebooks/markdown-it-py | #222 | NOT_EVALUATED, cond. 2 | wrong rendered string, but the fix was made in a different repository (mdurl PR 9), so this project's checkout never contains it |

Packages skipped by the rule "no result": rank 5 (kjd/idna), 17 (benjaminp/six), 27 (annotated-types), 28 (python-hyper/h11),
30 (pydantic/typing-inspection), 36 (boto/s3transfer), 41 (cpburnz/python-pathspec) in the first pass. In the second pass
(ranks 42 onward) the repository tox-dev/py-filelock (rank 42) could not be searched (HTTP 422) and was treated as skipped;
the first pass had stopped at that repository, so the second pass started at rank 42.

Counts by the condition that failed first: condition 1: 22, condition 3: 6, condition 2: 2, evaluable: 0.
