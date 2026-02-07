#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

log() {
  printf '%s\n' "$*"
}

install_with_brew() {
  local pkg="$1"
  if have_cmd brew; then
    brew list "$pkg" >/dev/null 2>&1 || brew install "$pkg"
    return 0
  fi
  return 1
}

install_with_apt() {
  local pkg="$1"
  if have_cmd apt-get; then
    sudo apt-get update
    sudo apt-get install -y "$pkg"
    return 0
  fi
  return 1
}

ensure_tool() {
  local cmd="$1"
  local brew_pkg="$2"
  local apt_pkg="$3"
  local manual="$4"

  if have_cmd "$cmd"; then
    log "ok: $cmd"
    return 0
  fi

  log "installing: $cmd"
  if [ -n "$brew_pkg" ] && install_with_brew "$brew_pkg"; then
    return 0
  fi
  if [ -n "$apt_pkg" ] && install_with_apt "$apt_pkg"; then
    return 0
  fi

  log "warning: could not auto-install $cmd. $manual"
  return 1
}

main() {
  cd "$repo_root"

  ensure_tool go "go" "golang" "Install Go manually from https://go.dev/dl/." || true
  ensure_tool python3 "python@3.12" "python3" "Install Python 3 manually." || true
  ensure_tool make "make" "make" "Install GNU Make manually." || true
  ensure_tool docker "docker" "docker.io" "Install Docker Desktop or Docker Engine manually." || true
  ensure_tool hyperfine "hyperfine" "hyperfine" "Install hyperfine manually." || true
  ensure_tool bats "bats-core" "bats" "Install bats-core manually." || true

  if have_cmd go; then
    log "installing Go tools"
    go install golang.org/x/perf/cmd/benchstat@latest
    go install github.com/seriousben/go-patch-cover/cmd/go-patch-cover@latest
  fi

  if have_cmd python3; then
    log "setting up Python virtualenv"
    if [ ! -d .venv ]; then
      python3 -m venv .venv
    fi
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install pytest pytest-cov jsonschema
  fi

  log "done. next steps:"
  log "  1) PATH=\"$repo_root/.venv/bin:\$PATH\" make test-scripts"
  log "  2) make test"
}

main "$@"
