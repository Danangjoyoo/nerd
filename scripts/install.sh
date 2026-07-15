#!/bin/sh
set -eu

usage() {
  echo "usage: $0 {claude|codex|cursor|all}" >&2
}

if [ "$#" -gt 1 ]; then
  usage
  exit 2
fi

case "${1:-all}" in
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

exec npx skills add danangjoyoo/nerd \
  --global --agent "$@" --skill '*' --yes
