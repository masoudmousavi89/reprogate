#!/usr/bin/env bash
# Linux + Docker checks for the checkout export (decision_079, F-052) and the writable /work. Run from anywhere; needs git, a running Docker daemon, uv or python3.8.
# Usage: bash labs/checkout-export-linux/run_checkout_export_linux.sh [WORK_DIR] [OUTPUT_MD]
# Everything it creates lives in WORK_DIR (default $HOME/coexp-work); raw output goes to OUTPUT_MD with home, work and repository paths masked.
# Lab images are built from the base image mirror.gcr.io/library/python:3.8-slim plus MarkupSafe wheels downloaded on the host and installed with --no-index
# (F-018: PyPI is not reachable from `docker build` in the cloud session).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; PROJ="$(cd "$HERE/../.." && pwd)"
WORK="${1:-$HOME/coexp-work}"; OUTMD="${2:-$HERE/results-linux-$(date +%Y-%m-%d).md}"
if command -v uv >/dev/null; then uv python install 3.8 -q; PY="$(uv python find 3.8)"; else PY="$(command -v python3.8)"; fi
[ -n "$PY" ] || { echo "Python 3.8 not found"; exit 2; }
BASE=mirror.gcr.io/library/python:3.8-slim; PIN=reprogate-jinja-pinned:export; UNP=reprogate-jinja-unpinned:export
mkdir -p "$WORK"; cd "$PROJ"; export PYTHONPATH="$HERE:$PROJ"
raw="$WORK/raw.md"; : > "$raw"
say() { printf '%s\n' "$*" >> "$raw"; }
section() { say ""; say "## $1"; say ""; say '```'; }
endsec() { say '```'; }
docker info >/dev/null 2>&1 || { echo "docker daemon not running"; exit 2; }
docker image inspect "$BASE" >/dev/null 2>&1 || docker pull -q "$BASE" >/dev/null
build() { # tag, requirement
  docker image inspect "$1" >/dev/null 2>&1 && return 0
  rm -rf "$WORK/ctx-$1"; mkdir -p "$WORK/ctx-$1"
  [ -x "$WORK/dl-venv/bin/python" ] || "$PY" -m venv "$WORK/dl-venv" >/dev/null
  "$WORK/dl-venv/bin/python" -m pip download -q --no-deps --only-binary=:all: --platform manylinux2014_x86_64 --python-version 3.8 "$2" -d "$WORK/ctx-$1/wheels" 2>/dev/null
  printf 'FROM %s\nCOPY wheels /wheels\nRUN pip install --no-cache-dir --no-index --find-links /wheels "%s" && rm -rf /wheels\n' "$BASE" "$2" > "$WORK/ctx-$1/Dockerfile"
  docker build -q -t "$1" "$WORK/ctx-$1" >/dev/null || { echo "image build failed: $1"; exit 2; }
}
build "$PIN" "MarkupSafe==2.0.1"; build "$UNP" "MarkupSafe>=2.1,<2.2"
rm -rf "$WORK"/out-* "$WORK"/ev-jinja; SRC="$WORK/jinja"; rm -rf "$SRC"
git clone -q https://github.com/pallets/jinja "$SRC" || { echo "clone failed"; exit 2; }

say "# Linux + Docker results for the checkout export and the writable /work (raw output of run_checkout_export_linux.sh)"
say ""
say "Environment: $(uname -sr), $("$PY" --version 2>&1), $(git --version), Docker $(docker version --format '{{.Server.Version}}' 2>/dev/null), base image $BASE, lab images $PIN (id $(docker image inspect -f '{{.Id}}' "$PIN" | cut -c1-19)) and $UNP (id $(docker image inspect -f '{{.Id}}' "$UNP" | cut -c1-19)); user $(id -un) (uid $(id -u)); source clone of pallets/jinja at HEAD $(git -C "$SRC" rev-parse --short HEAD)."

section "(a) F-050 reproducers d1-d4 (+ d0 walk-up probe) against the export checkout, host and Docker mode"; "$PY" "$HERE/attacks.py" "$BASE" >> "$raw" 2>&1; endsec
section "(b) oracle --before-sha/--after-sha in Docker mode; tree hashes against the Windows references"; "$PY" "$HERE/step_b.py" "$SRC" "$PIN" "$WORK/out-b" >> "$raw" 2>&1; endsec
section "(c) /work and the other clauses of req_005, docker inspect saved in docker-inspect-linux.json, compared with labs/checkout-sha-docker/docker-inspect-linux.json"; "$PY" "$HERE/step_c.py" "$SRC" "$PIN" "$WORK/out-c" "$HERE/docker-inspect-linux.json" "$PROJ/labs/checkout-sha-docker/docker-inspect-linux.json" >> "$raw" 2>&1; endsec
section "(d) POSIX export: exec bit, symlinks, case-only names (throwaway repository)"; "$PY" "$HERE/step_d.py" >> "$raw" 2>&1; endsec

# (e) jinja-843, six rows, through --checkout-sha in Docker mode (layout of labs/jinja-843/run_lab001.sh)
B=81825095d24f4dbccb40f787fff70db54989b91c; A=9a7dd7b28b50fd8adc019ab2702b50ae5c6ed782; EV="$WORK/ev-jinja"; mkdir -p "$EV"
CL=labs/jinja-843/claim.json; X="--allow-unverified-provenance"
section "(e) jinja-843 through --checkout-sha, Docker mode (six rows)"
{
"$PY" -m reprogate oracle --before-repo "$SRC" --after-repo "$SRC" --before-sha $B --after-sha $A --claim $CL --reproducer labs/jinja-843/repro.py --out "$EV/oracle" --sandbox docker --image "$PIN" $X | tail -2
"$PY" -m reprogate run --repo "$SRC" --checkout-sha $B --claim $CL --reproducer labs/jinja-843/repro.py --out "$EV/case_c_unpinned" --sandbox docker --image "$UNP" $X | tail -3
for f in f01_direct_raise f02_direct_deque_popleft f03_fake_traceback_stdout f04_subclass_override; do
  "$PY" -m reprogate run --repo "$SRC" --checkout-sha $B --claim $CL --reproducer labs/jinja-843/fixtures/$f.py --out "$EV/$f" --sandbox docker --image "$PIN" $X | tail -3
done
"$PY" tools/lab_summary.py --evidence "$EV" --expected labs/jinja-843/expected_outcomes.json --out "$EV/results.md" | tail -9
} >> "$raw" 2>&1
endsec
section "(e, static) file-writing calls in reproducers and fixtures under labs/"; "$PY" "$HERE/scan_cwd_writes.py" >> "$raw" 2>&1; endsec
sed "s#$HOME#<HOME>#g; s#$WORK#<WORK>#g; s#$PROJ#<REPO>#g" "$raw" > "$OUTMD"
sed -i "s#$HOME#<HOME>#g; s#$WORK#<WORK>#g; s#$PROJ#<REPO>#g" "$HERE/docker-inspect-linux.json" 2>/dev/null
echo "written $OUTMD"
