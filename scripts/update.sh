#!/usr/bin/env bash
set -euo pipefail

REF="${REF:-latest}"
GIT_BRANCH="${GIT_BRANCH:-master}"

log() { printf "\033[1;36m==>\033[0m %s\n" "$*"; }
die() {
  printf "\033[1;31mERROR: \033[0m %s\n" "$*" >&2
  exit 1
}

REPO_TOP="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "${REPO_TOP}" ]] || die "Run inside the repo."

cd "${REPO_TOP}"
log "Fetching..."
git fetch --tags --prune

if [[ "${REF}" == "latest" ]]; then
  TAG="$(git describe --tags "$(git rev-list --tags --max-count=1)" 2>/dev/null || true)"
  if [[ -z "${TAG}" ]]; then
    log "No tags found; using ${GIT_BRANCH}"
    git checkout -q "${GIT_BRANCH}"
    git pull --ff-only
  else
    log "Checking out latest tag: ${TAG}"
    git checkout -q "tags/${TAG}"
  fi
else
  log "Checking out ref: ${REF}"
  git checkout -q "${REF}"
  if git rev-parse --verify -q "refs/heads/${REF}" >/dev/null; then
    git pull --ff-only
  fi
fi

exec scripts/install.sh
