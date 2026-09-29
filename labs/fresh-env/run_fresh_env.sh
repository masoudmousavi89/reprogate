#!/usr/bin/env bash
# ReproGate fresh-environment-per-run runner (F-032) for Linux; port of run_fresh_env.ps1.
# Usage (repo root):  bash labs/fresh-env/run_fresh_env.sh [LAB_DIR] [PYTHON38]
# Needs the Lab #1 layout (LAB_DIR/jinja-before with .venv, LAB_DIR/jinja-after). The GitHub API is not reachable from the
# cloud environment, so labs/jinja-843/claim.json is used with --allow-unverified-provenance (qualifier PROVENANCE_UNVERIFIED).
# d01-d03 run against a COPY of the venv used as --env-template; the real .venv is used only as a read-only template for
# the last (oracle) step. Copies and the marker file are deleted at the end. Evidence goes to $HOME/rg-work, outside the repo.
set -u
LAB="${1:-$HOME/reprogate-lab}"; PY="${2:-python3.8}"
HERE="$(cd "$(dirname "$0")" && pwd)"; PROJ="$(cd "$HERE/../.." && pwd)"; R3="$PROJ/labs/adversarial-round3"
BEFORE="$LAB/jinja-before"; AFTER="$LAB/jinja-after"; VENV="$BEFORE/.venv"; PINNED="$VENV/bin/python"
CLAIM="$PROJ/labs/jinja-843/claim.json"; EXTRA="--allow-unverified-provenance"
for p in "$BEFORE" "$AFTER" "$PINNED" "$CLAIM"; do [ -e "$p" ] || { echo "MISSING: $p"; exit 2; }; done
STAMP="$(date +%Y%m%d-%H%M%S)"; EV="$HOME/rg-work/fresh-env-$STAMP"; TMP="$(mktemp -d)"
MARKER="${TMPDIR:-/tmp}/reprogate_r3_d02_marker.txt"
mkdir -p "$EV"; rm -f "$MARKER"
trap 'rm -rf "$TMP"; rm -f "$MARKER"' EXIT
cd "$PROJ"

treesha() { "$PY" -c "import sys; from reprogate.runner import tree_hash; print(tree_hash(sys.argv[1])[0])" "$1"; }
filesha() { sha256sum "$1" | cut -d' ' -f1; }
jget() { "$PY" -c "import json,sys; d=json.load(open(sys.argv[1])); 
for k in sys.argv[2].split('.'): d=d[k]
print(d)" "$1" "$2"; }
attack() { # name repro template python
  echo "--- $1"
  local t0=$(date +%s.%N)
  "$PY" -m reprogate run --repo "$BEFORE" --python "$4" --env-template "$3" --claim "$CLAIM" --reproducer "$2" --out "$EV/$1" --allow-host-execution $EXTRA | tail -3
  local t1=$(date +%s.%N)
  local copies; copies="$("$PY" -c "
import json,glob,sys
c=[json.load(open(f)).get('env_copy_seconds') for f in sorted(glob.glob(sys.argv[1]+'/runs/*/run.json'))]
c=[x for x in c if x is not None]
print(','.join(str(x) for x in c), round(sum(c)/len(c),2) if c else 'n/a')" "$EV/$1")"
  echo "COST $1 total_seconds=$(printf '%.1f' "$(echo "$t1 - $t0" | bc)") env_copy_seconds=${copies% *} avg=${copies##* }"
}

TMPL="$TMP/template"; cp -a "$VENV" "$TMPL"; TPY="$TMPL/bin/python"
echo "SYMLINKS_IN_TEMPLATE:"; find "$TMPL" -type l -printf '%P -> %l\n' | head -20
MK="$(ls "$TMPL"/lib/python*/site-packages/markupsafe/__init__.py)"
TSHA0="$(treesha "$TMPL")"; FSHA0="$(filesha "$MK")"

attack d01_tamper_dependency_file "$R3/d01_tamper_dependency_file.py" "$TMPL" "$TPY"
FSHA1="$(filesha "$MK")"
echo "D01 template_file_hash_unchanged=$([ "$FSHA0" = "$FSHA1" ] && echo True || echo False)"
REC_MODE="$(jget "$EV/d01_tamper_dependency_file/environment.json" environment_isolation.mode)"
REC_HASH="$(jget "$EV/d01_tamper_dependency_file/environment.json" environment_isolation.template_tree_sha256)"
echo "D01 recorded_mode=$REC_MODE recorded_hash_equals_independent=$([ "$REC_HASH" = "$TSHA0" ] && echo True || echo False)"

attack d01_again "$R3/d01_tamper_dependency_file.py" "$TMPL" "$TPY"
REC2_HASH="$(jget "$EV/d01_again/environment.json" environment_isolation.template_tree_sha256)"
echo "DETERMINISM same_template_hash=$([ "$REC_HASH" = "$REC2_HASH" ] && echo True || echo False)"

attack d02_sitecustomize_persistence "$R3/d02_sitecustomize_persistence.py" "$TMPL" "$TPY"
echo "D02 marker_writes=$( [ -f "$MARKER" ] && wc -c < "$MARKER" || echo 0 )"

attack d03_poison_dependency_claim_text "$R3/d03_poison_dependency_claim_text.py" "$TMPL" "$TPY"
O3="$EV/d03_poison_dependency_claim_text/outcome.json"
echo "D03 completed=$(jget "$O3" counts.completed) clean_completion_runs=$(jget "$O3" counts.clean_completion_runs)"
echo "TEMPLATE tree_hash_unchanged_after_all_attacks=$([ "$(treesha "$TMPL")" = "$TSHA0" ] && echo True || echo False)"

# jinja oracle with the REAL venv as a read-only template
echo "--- jinja_oracle_real_venv_as_template"
REAL0="$(treesha "$VENV")"
T0=$(date +%s.%N)
"$PY" -m reprogate oracle --before-repo "$BEFORE" --after-repo "$AFTER" --python "$PINNED" --env-template "$VENV" --claim "$CLAIM" --reproducer "$PROJ/labs/jinja-843/repro.py" --out "$EV/jinja_oracle" --allow-host-execution $EXTRA | tail -3
T1=$(date +%s.%N)
echo "COST jinja_oracle total_seconds=$(printf '%.1f' "$(echo "$T1 - $T0" | bc)")"
echo "REAL_VENV tree_hash_unchanged=$([ "$(treesha "$VENV")" = "$REAL0" ] && echo True || echo False)"
for b in before after; do
  "$PY" -m reprogate inspect --evidence "$EV/jinja_oracle/$b" | grep -E "outcome  |invariants" | sed "s/^ */$b: /"
done
echo; echo "Evidence folder: <HOME>/rg-work/fresh-env-$STAMP"
