# Random sample v3 (protocol, fixed before the draw)

Purpose: the bugs for the measurements of `STOP_CRITERIA.md`. Two stages, because the v2 sample
(`labs/sample-2026-09/`, F-022) gave 4 eligible draws out of 16 and only 1 of those 4 could be evaluated: with the v2 pools
alone, 10 evaluable bugs would need on the order of 160 draws.

- **WIDE** (coverage, metric M4 only): the v2 pool definitions, unchanged (`labs/sample-2026-09/PROTOCOL.md`: `LIB` and
  `APP`, eligibility E1 and E2 with Amendment 1). No reproducer is written for these draws.
- **NARROW** (bugs for M1 and M2): pure-Python libraries, where the current tool (exception claims, hermetic reproducer)
  can be applied.

## Parameters

- Seed: `202609293`. Each pool uses its own RNG seeded from the seed and the pool name, so one pool's draws do not shift
  another's.
- WIDE: exactly 20 draws from `LIB` and 20 from `APP`.
- NARROW: draws continue until 12 evaluable bugs are collected, with a hard cap of 60 draws. If fewer than 12 are
  collected, the sample is smaller; it is not extended (below the minimums of `STOP_CRITERIA.md` the verdict is
  INCONCLUSIVE).
- Excluded repositories (NARROW and WIDE): every repository of labs 1-9 and of the v2 draws: pallets/jinja,
  tkem/cachetools, astanin/python-tabulate, more-itertools/more-itertools, grantjenks/python-sortedcontainers,
  dateutil/dateutil, pallets/click, theOehrly/Fast-F1, taurus-org/taurus, httpie/cli. A draw that lands on one of them
  is recorded as excluded and counts as a draw.

## NARROW pool

1. Package list: a snapshot of the 1000 most downloaded PyPI packages (public dataset `top-pypi-packages`), committed as
   a file in this folder before the draw, with its source URL and download date.
2. Filter: packages whose latest release has a `py3-none-any` wheel. The GitHub repository comes from the package's
   PyPI project URLs (source or homepage pointing to github.com); packages without one are removed. The filtered list is
   committed before the draw.
3. One draw = the RNG picks one package from the filtered list, then one closed issue of its repository whose body
   contains `Traceback (most recent call last)`. A package with no such issue is recorded as not eligible (the draw counts).
4. Eligible = E1 and E2 (v2 definitions) and the evaluability checklist below.

## Evaluability checklist (both pools)

Answered from the issue text and the fix diff, recorded per draw with the reason. A draw is evaluable only if the bug
needs none of:

1. a network service or external API,
2. a GUI or display,
3. unsafe input (for example a user's pickle file),
4. a dependency that cannot be installed at a stated version.

M4 = evaluable WIDE draws divided by all WIDE draws whose body contains a Python traceback (`STOP_CRITERIA.md`).

## Rules (as in v2)

- The draw is executed exactly once per pool; the first result is the sample. Seed, pool definitions, list snapshots and
  search queries are not changed afterwards. Nothing is redrawn.
- Every draw is recorded (`draws-*.json` in this folder), eligible or not.
- The sampler changes needed for NARROW (`tools/sample_issues.py`) and the list snapshots are committed before the draw.
- Each bug runs on the Python version its project needs at the affected commit; the version is recorded.
- The draw runs where the GitHub API is reachable (the Linux session gets HTTP 403).

## Limits stated up front

NARROW is biased toward simpler, self-contained bugs by construction. That is acceptable for M1 and M2, which measure
discrimination, but M4 is computed from WIDE only.
