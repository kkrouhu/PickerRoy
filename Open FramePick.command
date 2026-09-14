#!/bin/zsh
set -e
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/framepick ]]; then
  osascript -e 'display dialog "FramePick has not been installed yet. Run Install FramePick.command first." buttons {"OK"} default button "OK" with icon caution'
  exit 1
fi
exec .venv/bin/framepick

