#!/bin/zsh
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
if [[ "$(uname -s)" == "Darwin" ]]; then
  .venv/bin/pip install -e '.[mac,dev]'
else
  .venv/bin/pip install -e '.[dev]'
fi
osascript -e 'display dialog "FramePick installation is complete. Double-click Open FramePick.command to start." buttons {"OK"} default button "OK"'

