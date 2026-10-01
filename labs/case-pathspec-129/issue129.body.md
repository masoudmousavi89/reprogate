`GitIgnoreSpec` re-includes a file through a negation pattern even when a parent directory is excluded, which git forbids ("It is not possible to re-include a file if a parent directory of that file is excluded").

## Repro (pathspec 1.1.1)

```python
from pathspec import GitIgnoreSpec

spec = GitIgnoreSpec.from_lines(["build", "!keep.log"])
spec.match_file("build/keep.log")   # -> False (treated as NOT ignored)
```

`build/keep.log` should be ignored: `build` excludes the whole `build` directory, and `!keep.log` cannot re-include a file whose parent directory is excluded.

## Verified against real git

With `.gitignore`:

```
build
!keep.log
```

and a real `build/keep.log` on disk:

```
$ git add build/keep.log
The following paths are ignored by one of your .gitignore files:
build

$ git status --porcelain --ignored
!! build/
```

git treats `build/keep.log` as ignored (the entire `build/` is excluded); `git check-ignore build/keep.log` agrees.

## The distinction it misses

The bug is the difference between excluding a *directory* and excluding a directory's *contents*:

| `.gitignore`                     | path             | git       | `GitIgnoreSpec.match_file` |
|----------------------------------|------------------|-----------|----------------------------|
| `build` + `!keep.log`            | `build/keep.log` | ignored   | not ignored ❌             |
| `a` + `!keep.log`                | `a/keep.log`     | ignored   | not ignored ❌             |
| `build/*` + `!build/keep.log`    | `build/keep.log` | re-included | re-included ✅           |

`build/*` excludes only the contents, so re-inclusion is allowed and pathspec gets it right. `build` excludes the directory itself, so re-inclusion must fail.

## Root cause (as far as I can tell)

`GitIgnoreSpec` matching is flat: `match_file` matches the full path against every pattern and takes the last match, so a file-level negation (`!keep.log`, no directory marker) overrides a directory-level exclusion (`build`, matched with a directory marker). git evaluates the path hierarchically, so once a directory is excluded nothing beneath it can be re-included. Telling the two cases apart seems to need ancestor-directory awareness rather than a flat last-match.

## Environment

- pathspec 1.1.1
- Python 3.14.3
- git 2.55.0

Happy to help with tests or a fix if you have a preferred approach across the backends.
