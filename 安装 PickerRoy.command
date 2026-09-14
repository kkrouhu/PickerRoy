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
osascript -e 'display dialog "PickerRoy 安装完成。现在可以双击 PickerRoy.app 启动。" buttons {"好"} default button "好"'
