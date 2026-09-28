#!/usr/bin/env bash
# LAB-001 runner for Linux/macOS. Mirrors run_lab001.ps1. Needs git, network, uv (or python3.8 on PATH).
# WARNING: prototype has NO sandbox; it runs repro.py and fixtures/*.py on this machine.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; PROJ="$(cd "$HERE/../.." && pwd)"
LAB="${1:-$HOME/reprogate-lab}"; mkdir -p "$LAB"
if command -v uv >/dev/null; then uv python install 3.8 -q; PY="$(uv python find 3.8)"; else PY="$(command -v python3.8)"; fi
[ -n "$PY" ] || { echo "Python 3.8 not found"; exit 2; }
read -r -p "No sandbox. Type YES to continue: " a; [ "$a" = YES ] || exit 1
A=81825095d24f4dbccb40f787fff70db54989b91c; F=9a7dd7b28b50fd8adc019ab2702b50ae5c6ed782
[ -d "$LAB/jinja" ] || git clone -q https://github.com/pallets/jinja "$LAB/jinja"
[ -d "$LAB/jinja-before" ] || git -C "$LAB/jinja" worktree add -f ../jinja-before $A
[ -d "$LAB/jinja-after" ] || git -C "$LAB/jinja" worktree add -f ../jinja-after $F
B="$LAB/jinja-before"
mkvenv() { "$PY" -m venv "$B/$1" && "$B/$1/bin/python" -m pip install -q "$2"; }
[ -x "$B/.venv/bin/python" ] || mkvenv .venv "MarkupSafe==2.0.1"
[ -x "$B/.venv-unpinned/bin/python" ] || mkvenv .venv-unpinned "MarkupSafe>=2.1,<2.2"
PIN="$B/.venv/bin/python"; UNP="$B/.venv-unpinned/bin/python"
EV="$HERE/evidence-$(date +%Y%m%d-%H%M%S)"; mkdir -p "$EV"; cd "$PROJ"
CLAIM="$HERE/claim.json"; EXTRA="--allow-unverified-provenance"
if "$PY" tools/fetch_issue.py --out "$HERE/issue843" && "$PY" -m reprogate claim-check --claim "$CLAIM" --issue-body "$HERE/issue843.body.md" --out "$HERE/claim.frozen.json"; then
  CLAIM="$HERE/claim.frozen.json"; EXTRA=""; else echo "Provenance NOT verified (recorded)."; fi
"$PY" -m reprogate oracle --before-repo "$B" --after-repo "$LAB/jinja-after" --python "$PIN" --claim "$CLAIM" --reproducer "$HERE/repro.py" --out "$EV/oracle" --allow-host-execution $EXTRA
"$PY" -m reprogate run --repo "$B" --python "$UNP" --claim "$CLAIM" --reproducer "$HERE/repro.py" --out "$EV/case_c_unpinned" --allow-host-execution $EXTRA
for f in f01_direct_raise f02_direct_deque_popleft f03_fake_traceback_stdout f04_subclass_override; do
  "$PY" -m reprogate run --repo "$B" --python "$PIN" --claim "$CLAIM" --reproducer "$HERE/fixtures/$f.py" --out "$EV/$f" --allow-host-execution $EXTRA
done
"$PY" tools/lab_summary.py --evidence "$EV" --expected "$HERE/expected_outcomes.json" --out "$EV/results.md"
