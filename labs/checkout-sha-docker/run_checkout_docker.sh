#!/usr/bin/env bash
# Linux + Docker checks for the checkout-by-SHA change (req_005). Run from anywhere; needs git, docker (daemon running), uv or python3.8.
# Usage: bash labs/checkout-sha-docker/run_checkout_docker.sh [WORK_DIR] [OUTPUT_MD]
# Everything it creates lives in WORK_DIR (default $HOME/cosha-work); the raw output is written to OUTPUT_MD with the home path masked as <HOME>.
# The base image mirror.gcr.io/library/python:3.8-slim is used because Docker Hub rate-limits and PyPI is unreachable from `docker build` in the
# cloud session (F-018): MarkupSafe 2.0.1 is downloaded on the host as a wheel and installed with --no-index.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; PROJ="$(cd "$HERE/../.." && pwd)"
WORK="${1:-$HOME/cosha-work}"; OUTMD="${2:-$HERE/results-linux-$(date +%Y-%m-%d).md}"
if command -v uv >/dev/null; then uv python install 3.8 -q; PY="$(uv python find 3.8)"; else PY="$(command -v python3.8)"; fi
[ -n "$PY" ] || { echo "Python 3.8 not found"; exit 2; }
BASE=mirror.gcr.io/library/python:3.8-slim; IMG=reprogate-jinja-pinned:cosha
mkdir -p "$WORK"; cd "$PROJ"; export PYTHONPATH="$HERE:$PROJ"
raw="$WORK/raw.md"; : > "$raw"
say() { printf '%s\n' "$*" >> "$raw"; }
section() { say ""; say "## $1"; say ""; say '```'; }
endsec() { say '```'; }

docker info >/dev/null 2>&1 || { echo "docker daemon not running"; exit 2; }
docker image inspect "$BASE" >/dev/null 2>&1 || docker pull -q "$BASE" >/dev/null
if ! docker image inspect "$IMG" >/dev/null 2>&1; then
  "$PY" -m venv "$WORK/dl-venv" && "$WORK/dl-venv/bin/python" -m pip download -q --no-deps --only-binary=:all: --platform manylinux2014_x86_64 --python-version 3.8 "MarkupSafe==2.0.1" -d "$WORK/ctx/wheels"
  printf 'FROM %s\nCOPY wheels /wheels\nRUN pip install --no-cache-dir --no-index --find-links /wheels "MarkupSafe==2.0.1" && rm -rf /wheels\n' "$BASE" > "$WORK/ctx/Dockerfile"
  docker build -q -t "$IMG" "$WORK/ctx" >/dev/null || { echo "image build failed"; exit 2; }
fi
SRC="$WORK/jinja"; rm -rf "$SRC"; git clone -q https://github.com/pallets/jinja "$SRC" || { echo "clone failed"; exit 2; }

say "# Linux + Docker results for the checkout-by-SHA change (raw output of run_checkout_docker.sh)"
say ""
say "Environment: $(uname -sr), $("$PY" --version 2>&1), $(git --version), Docker $(docker version --format '{{.Server.Version}}' 2>/dev/null), base image $BASE, lab image $IMG (image id $(docker image inspect -f '{{.Id}}' "$IMG" | cut -c1-19)); user $(id -un) (uid $(id -u)); source clone of pallets/jinja at HEAD $(git -C "$SRC" rev-parse --short HEAD)."

section "(a) oracle --before-sha/--after-sha in Docker mode"; "$PY" "$HERE/step_a.py" "$SRC" "$IMG" "$WORK/out-a" >> "$raw" 2>&1; endsec
section "(b) what the container sees"; "$PY" "$HERE/step_b.py" "$SRC" "$IMG" >> "$raw" 2>&1; endsec
section "(c) write attempts through the real tool (real gate), Docker mode"; "$PY" "$HERE/step_c.py" "$SRC" "$IMG" "$WORK/out-c" >> "$raw" 2>&1; endsec
section "(d) and (d-docker) reachability of the source .git from a worktree (throwaway repository)"; "$PY" "$HERE/host_exposure.py" "$BASE" >> "$raw" 2>&1; endsec
section "(e) req_005 clauses, Docker mode, docker inspect saved in docker-inspect-linux.json"; "$PY" "$HERE/step_e.py" "$SRC" "$IMG" "$WORK/out-e" "$HERE/docker-inspect-linux.json" >> "$raw" 2>&1; endsec
section "(f) worktree vs git archive"; "$PY" "$HERE/step_f.py" "$SRC" >> "$raw" 2>&1; endsec
sed "s#$HOME#<HOME>#g; s#$WORK#<WORK>#g" "$raw" > "$OUTMD"
echo "written $OUTMD"
