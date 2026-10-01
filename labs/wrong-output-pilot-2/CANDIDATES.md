# Pilot 2 candidates: every pull request examined, in selection order

Selection as fixed in `PROTOCOL.md` (commit 01a327e, before this search): packages of `labs/sample-v3/narrow-packages.json` in
ascending `rank`, minus the excluded repositories and every repository named in pilot 1's `CANDIDATES.md`; per package
the newest merged pull requests linked to an issue (`is:pr is:merged linked:issue`), at most 3; a pull request passes the file
screen if it adds, in a test file, an assertion on a returned value compared with a literal; stop at 5 evaluable or 40
pull requests examined. Search run 2026-10-01 through the unauthenticated GitHub API (the run waited for the hourly rate limit).

Result: **40 pull requests examined, 0 evaluable.** The sample was not extended and the method was not changed after seeing
this result. See "Screening mistake and its correction" below: the list is the corrected one.

How the file screen worked: a regular expression over the added lines of test files (`assert <expr> == <literal>` and
`assertEqual(<expr>, <literal>)`, literals being numbers, strings, containers, True, False, None, bytes). It is a
heuristic: it can miss other assertion styles (`assert x is None`, truthiness, `pytest.raises`) and it passed 16 pull requests
that were then read. How those were judged: by reading the linked issue (some only in part, marked "read in part") and the
pull request metadata, before any run. The reading of "can be written as Python literals" is the maintainer's and can
be disputed row by row.

| # | rank | project | pull request | verdict | reason |
|---|---|---|---|---|---|
| 1 | 57 | aio-libs/multidict | #1582 | NOT_EVALUATED, cond. 1 and 3 | issue #1581 is a use after free in the C extension; no stated values and memory-unsafe |
| 2 | 57 | aio-libs/multidict | #1580 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 3 | 57 | aio-libs/multidict | #1573 | NOT_EVALUATED, cond. 1 | issue #1535 is an interpreter assertion abort with a str subclass; no stated values |
| 4 | 58 | aio-libs/propcache | #307 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 5 | 58 | aio-libs/propcache | #302 | NOT_EVALUATED, cond. 1 | issue #244 is a performance regression; the pull request passes build flags |
| 6 | 58 | aio-libs/propcache | #240 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 7 | 59 | fsspec/s3fs | #1048 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 8 | 59 | fsspec/s3fs | #1047 | NOT_EVALUATED, cond. 3 | issue #838 needs an S3 service |
| 9 | 59 | fsspec/s3fs | #1042 | NOT_EVALUATED, cond. 3 | issue #982 needs an S3 service and concurrency |
| 10 | 60 | fastapi/fastapi | #15077 | NOT_EVALUATED, cond. 1 | no linked issue was parsed from the pull request text (read in part); the bug is in the generated OpenAPI schema, not a returned value |
| 11 | 60 | fastapi/fastapi | #14794 | NOT_EVALUATED, cond. 1 | issue #10127 (read in part) is a compatibility request about a type hint, no stated expected and actual value |
| 12 | 60 | fastapi/fastapi | #14681 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 13 | 62 | python-poetry/tomlkit | #620 | NOT_EVALUATED, cond. 1 | issue #619 (read in part) reports a missing fold argument seen as a PyPy test failure, no stated expected value |
| 14 | 62 | python-poetry/tomlkit | #597 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 15 | 62 | python-poetry/tomlkit | #563 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 16 | 63 | aio-libs/frozenlist | #776 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 17 | 63 | aio-libs/frozenlist | #770 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 18 | 63 | aio-libs/frozenlist | #766 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 19 | 64 | python-jsonschema/jsonschema-specifications | #151 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 20 | 65 | pyasn1/pyasn1 | #111 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 21 | 65 | pyasn1/pyasn1 | #108 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 22 | 65 | pyasn1/pyasn1 | #102 | NOT_EVALUATED, cond. 1 | closest case: issue #81 states that GeneralizedTime.asDateTime returns 2016-08-06 11:59:52.018000+00:00 instead of 11:59:52.180000+00:00 for the payload 20160806115952.18Z, and the fix adds tests; but both values are datetime objects, not Python literals under the claim format |
| 23 | 66 | pypa/wheel | #695 | NOT_EVALUATED, cond. 1 | issue #692: the wheel tags command writes an invalid ZIP64 header for files over 4 GB; file output, no returned value stated |
| 24 | 66 | pypa/wheel | #694 | NOT_EVALUATED, cond. 1 | issue #570 is a feature request (local version identifiers) |
| 25 | 66 | pypa/wheel | #690 | NOT_EVALUATED, cond. 1 | issue #643 asks why the converted Metadata-Version changes to 2.4; no call or expected literal stated |
| 26 | 67 | python-websockets/websockets | #1752 | NOT_EVALUATED, cond. 1 | issue #1749 is about reference cycles keeping closed connections alive; no returned value |
| 27 | 67 | python-websockets/websockets | #1745 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 28 | 67 | python-websockets/websockets | #1743 | NOT_EVALUATED, cond. 1 | issue #816 is a ValueError (unsupported HTTP version); an exception, no expected and actual value |
| 29 | 68 | aio-libs/aiohappyeyeballs | #249 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 30 | 68 | aio-libs/aiohappyeyeballs | #247 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 31 | 68 | aio-libs/aiohappyeyeballs | #229 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 32 | 69 | executablebooks/mdurl | #9 | NOT_EVALUATED, cond. 2 | closest case: the linked issue (markdown-it-py #222) states render() returns a string with surrogates and gives both strings, but it lives in another repository and names render(), while this repository's regression test calls decode(); the issue's call is not exercised by the test |
| 33 | 70 | aio-libs/aiosignal | #723 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 34 | 75 | python-trio/sniffio | #45 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 35 | 76 | python/importlib_metadata | #543 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 36 | 76 | python/importlib_metadata | #521 | NOT_EVALUATED, cond. 1 | issue #520 is intermittent errors under multiprocessing; no stated values |
| 37 | 76 | python/importlib_metadata | #519 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 38 | 77 | pypa/trove-classifiers | #229 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 39 | 77 | pypa/trove-classifiers | #215 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |
| 40 | 77 | pypa/trove-classifiers | #201 | NOT_EVALUATED, file screen | no assertion on a returned value compared with a literal was added to a test file |

Packages skipped: rank 61 python-jsonschema/referencing (no result).

Counts: file screen failed 24; passed the screen 16: condition 1 12, condition 1 and 3 1, condition 3 2, condition 2 1; evaluable 0.

## Screening mistake and its correction

The protocol excludes "every repository that appears in `labs/wrong-output-pilot/CANDIDATES.md`". My first screening script
read only the table rows of that file and not the paragraph that names the packages skipped in pilot 1 ("no result").
The first run therefore examined 40 pull requests of which 21 came from 7 excluded repositories (kjd/idna, benjaminp/six, python-hyper/h11, pydantic/typing-inspection, boto/s3transfer, cpburnz/python-pathspec, annotated-types/annotated-types),
Six of them were removed by the first correction; the seventh, annotated-types (3 pull requests), which pilot 1 names without its owner prefix, was still missed and removed by a second correction.
It was found while writing this table, before anything was committed. The correction removed every pull request of those
repositories, kept the others examined by the first run (they are valid) and continued down the same rank order until 40
were examined. The table above is the corrected list. The removed pull requests and the first run are described in
`RESULTS.md`.
