#!/bin/sh
set -eu

usage() {
  echo "usage: $0 {claude|codex|cursor|all} [--ufast]" >&2
}

if [ "$#" -gt 2 ]; then
  usage
  exit 2
fi

target=${1:-all}
ufast=${2:-}
if [ -n "$ufast" ] && [ "$ufast" != "--ufast" ]; then
  usage
  exit 2
fi
if [ "$ufast" = "--ufast" ] && [ "$target" != "codex" ] && [ "$target" != "all" ]; then
  echo "error: Nerd UFast tool integration is currently verified only for Codex" >&2
  exit 2
fi

case "$target" in
  claude)
    set -- claude-code
    ;;
  codex)
    set -- codex
    ;;
  cursor)
    set -- cursor
    ;;
  all)
    set -- claude-code codex cursor
    ;;
  *)
    usage
    exit 2
    ;;
esac

if ! command -v npx >/dev/null 2>&1; then
  echo "error: npx is required (install Node.js first)" >&2
  exit 127
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 is required to configure nerd-smart hooks" >&2
  exit 127
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

npx skills add danangjoyoo/nerd \
  --global --agent "$@" --skill '*' --yes

python3 "$script_dir/install_hooks.py" "$@"

if [ "$ufast" = "--ufast" ]; then
  python3 "$script_dir/install_ufast.py"
fi
