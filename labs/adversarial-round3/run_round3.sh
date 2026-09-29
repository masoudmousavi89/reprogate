#!/usr/bin/env bash
# ReproGate adversarial round 3 runner for Linux (equivalent of run_round3.ps1, plus a Docker mode).
# Usage (repo root):  bash labs/adversarial-round3/run_round3.sh host|docker [LAB_DIR] [PYTHON38] [IMAGE]
#   LAB_DIR  default $HOME/reprogate-lab: needs jinja-before (with .venv) and jinja-after (Lab #1 layout).
#   host mode : NO SANDBOX; d01-d03 run against COPIES of the venv in a temp dir, never the real venv.
#   docker mode: IMAGE holds Python 3.8 and MarkupSafe==2.0.1 (default reprogate-jinja-pinned:local).
# Provenance of labs/jinja-843/claim.json is unverified here (GitHub API 403), so --allow-unverified-provenance is used.
set -u
MODE="${1:-host}"; LAB="${2:-$HOME/reprogate-lab}"; PY="${3:-python3.8}"; IMAGE="${4:-reprogate-jinja-pinned:local}"
HERE="$(cd "$(dirname "$0")" && pwd)"; PROJ="$(cd "$HERE/../.." && pwd)"
B="$LAB/jinja-before"; A="$LAB/jinja-after"; CLAIM="$PROJ/labs/jinja-843/claim.json"
EV="$HERE/evidence-$MODE-$(date +%Y%m%d-%H%M%S)"; TMP="$(mktemp -d)"; MARK="${TMPDIR:-/tmp}/reprogate_r3_d02_marker.txt"
mkdir -p "$EV"; rm -f "$MARK"; cd "$PROJ"
trap 'rm -rf "$TMP"; rm -f "$MARK"' EXIT
sha() { sha256sum "$1" | cut -d' ' -f1; }
envsha() { "$PY" -c "import sys; from reprogate.runner import capture_environment; print(capture_environment(sys.argv[1])[1])" "$1"; }
if [ "$MODE" = docker ]; then
  SBX="--sandbox docker --image $IMAGE"
  dsha() { docker run --rm --network none "$IMAGE" python -c "import hashlib,markupsafe;print(hashlib.sha256(open(markupsafe.__file__,'rb').read()).hexdigest())"; }
  dsite() { docker run --rm --network none "$IMAGE" python -c "import os,markupsafe;print(os.path.exists(os.path.join(os.path.dirname(os.path.dirname(markupsafe.__file__)),'sitecustomize.py')))"; }
  echo "IMAGE_MARKUPSAFE_SHA_BEFORE=$(dsha)"
else
  SBX=""; VENV="$B/.venv"
fi
attack() { # name repro python
  echo "--- $1 ($MODE)"
  if [ "$MODE" = docker ]; then
    "$PY" -m reprogate run --repo "$B" --claim "$CLAIM" --reproducer "$2" --out "$EV/$1" $SBX --allow-unverified-provenance
  else
    "$PY" -m reprogate run --repo "$B" --python "$3" --claim "$CLAIM" --reproducer "$2" --out "$EV/$1" --allow-host-execution --allow-unverified-provenance
  fi
}
venvcopy() { cp -a "$VENV" "$TMP/$1"; echo "$TMP/$1/bin/python"; }
recenv() { "$PY" -c "import json,sys; print(json.load(open(sys.argv[1]))['environment_sha256'])" "$EV/$1/outcome.json"; }

if [ "$MODE" = host ]; then
  P1="$(venvcopy venv_d01)"; F1="$(dirname "$TMP/venv_d01"/lib/python*/site-packages/markupsafe/__init__.py)/__init__.py"
  E0="$(envsha "$P1")"; S0="$(sha "$F1")"
  attack d01_tamper_dependency_file "$HERE/d01_tamper_dependency_file.py" "$P1"
  S1="$(sha "$F1")"; E1="$(envsha "$P1")"
  echo "D01 file_hash_changed=$([ "$S0" != "$S1" ] && echo True || echo False) env_sha_before_equals_after=$([ "$E0" = "$E1" ] && echo True || echo False) recorded_env_equals_after=$([ "$(recenv d01_tamper_dependency_file)" = "$E1" ] && echo True || echo False)"
  P2="$(venvcopy venv_d02)"
  attack d02_sitecustomize_persistence "$HERE/d02_sitecustomize_persistence.py" "$P2"
  echo "D02 marker_writes=$( [ -f "$MARK" ] && wc -c < "$MARK" || echo 0 )"
  P3="$(venvcopy venv_d03)"
  attack d03_poison_dependency_claim_text "$HERE/d03_poison_dependency_claim_text.py" "$P3"
else
  attack d01_tamper_dependency_file "$HERE/d01_tamper_dependency_file.py" ""
  echo "D01 image_markupsafe_sha_after=$(dsha)"
  attack d02_sitecustomize_persistence "$HERE/d02_sitecustomize_persistence.py" ""
  echo "D02 image_has_sitecustomize=$(dsite)"
  attack d03_poison_dependency_claim_text "$HERE/d03_poison_dependency_claim_text.py" ""
  echo "D03 image_markupsafe_sha_after=$(dsha)"
fi

echo "--- d04_malicious_issue ($MODE)"
MAL="$HERE/malicious-issue"; FROZEN="$EV/d04_claim.frozen.json"; R4="$HERE/d04_malicious_issue_reproducer.py"
"$PY" -m reprogate claim-check --claim "$MAL/claim.json" --issue-body "$MAL/issue.body.md" --out "$FROZEN"
if [ "$MODE" = docker ]; then
  "$PY" -m reprogate run --repo "$B" --claim "$FROZEN" --reproducer "$R4" --out "$EV/d04_run" $SBX
  "$PY" -m reprogate oracle --before-repo "$B" --after-repo "$A" --claim "$FROZEN" --reproducer "$R4" --out "$EV/d04_oracle" $SBX
else
  "$PY" -m reprogate run --repo "$B" --python "$VENV/bin/python" --claim "$FROZEN" --reproducer "$R4" --out "$EV/d04_run" --allow-host-execution
  "$PY" -m reprogate oracle --before-repo "$B" --after-repo "$A" --python "$VENV/bin/python" --claim "$FROZEN" --reproducer "$R4" --out "$EV/d04_oracle" --allow-host-execution
fi
echo; echo "Evidence folder: $EV"
