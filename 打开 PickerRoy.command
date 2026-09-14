#!/bin/zsh
set -e
cd "$(dirname "$0")"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
if [[ ! -x .venv/bin/pickerroy ]]; then
  osascript -e 'display dialog "PickerRoy 尚未安装。请先运行一次“安装 PickerRoy.command”。" buttons {"好"} default button "好" with icon caution'
  exit 1
fi
exec .venv/bin/pickerroy
