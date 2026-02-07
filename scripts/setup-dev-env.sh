#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

mode="local"
subset_csv="all"
apt_updated=0

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

log() {
  printf '%s\n' "$*"
}

install_with_brew() {
  local pkg="$1"
  if [ "$mode" = "ci" ]; then
    return 1
  fi
  if have_cmd brew; then
    if ! brew list "$pkg" >/dev/null 2>&1; then
      if ! brew install "$pkg"; then
        return 1
      fi
    fi
    return 0
  fi
  return 1
}

install_with_apt() {
  local pkg="$1"
  if have_cmd apt-get; then
    if [ "$apt_updated" -eq 0 ]; then
      if ! sudo apt-get update; then
        return 1
      fi
      apt_updated=1
    fi
    if ! sudo apt-get install -y "$pkg"; then
      return 1
    fi
    return 0
  fi
  return 1
}

usage() {
  cat <<'EOF'
Usage: bash scripts/setup-dev-env.sh [--ci] [--subset LIST]

Options:
  --ci             CI-friendly mode (skip Homebrew installs, prefer apt)
  --subset LIST    Comma-separated install groups

Subset groups:
  all              Everything (default)
  core             go, python3, make
  docker           docker cli/engine
  shell-test       bats
  benchmark-tools  hyperfine + benchstat
  python-test      venv + pytest + pytest-cov + jsonschema
  go-tools         go-patch-cover

Examples:
  bash scripts/setup-dev-env.sh
  bash scripts/setup-dev-env.sh --subset core,python-test
  bash scripts/setup-dev-env.sh --ci --subset python-test,shell-test,benchmark-tools
EOF
}

has_subset() {
  local needle="$1"
  if [ "$subset_csv" = "all" ]; then
    return 0
  fi
  case ",$subset_csv," in
    *",$needle,"*) return 0 ;;
    *) return 1 ;;
  esac
}

parse_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --ci)
        mode="ci"
        ;;
      --subset)
        shift
        if [ "$#" -eq 0 ]; then
          echo "missing value for --subset" >&2
          usage
          exit 1
        fi
        subset_csv="$1"
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "unknown argument: $1" >&2
        usage
        exit 1
        ;;
    esac
    shift
  done
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
  parse_args "$@"
  cd "$repo_root"

  if has_subset core; then
    ensure_tool go "go" "golang" "Install Go manually from https://go.dev/dl/." || true
    ensure_tool python3 "python@3.12" "python3" "Install Python 3 manually." || true
    ensure_tool make "make" "make" "Install GNU Make manually." || true
  fi

  if has_subset docker; then
    ensure_tool docker "docker" "docker.io" "Install Docker Desktop or Docker Engine manually." || true
  fi

  if has_subset benchmark-tools; then
    ensure_tool hyperfine "hyperfine" "hyperfine" "Install hyperfine manually." || true
  fi

  if has_subset shell-test; then
    ensure_tool bats "bats-core" "bats" "Install bats-core manually." || true
  fi

  if has_subset benchmark-tools && have_cmd go; then
    log "installing Go tools"
    go install golang.org/x/perf/cmd/benchstat@latest
  fi

  if has_subset go-tools && have_cmd go; then
    log "installing Go patch coverage tool"
    go install github.com/seriousben/go-patch-cover/cmd/go-patch-cover@latest
  fi

  if has_subset python-test && have_cmd python3; then
    log "setting up Python virtualenv"
    if [ ! -d .venv ]; then
      python3 -m venv .venv
    fi
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install pytest pytest-cov jsonschema
  fi

  log "done (mode=$mode, subset=$subset_csv). next steps:"
  if has_subset python-test; then
    log "  1) PATH=\"$repo_root/.venv/bin:\$PATH\" make test-scripts"
  fi
  log "  2) make test"
}

main "$@"
