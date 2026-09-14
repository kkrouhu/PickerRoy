from __future__ import annotations

import argparse
import os
import platform
import shutil
from pathlib import Path

import PyInstaller.__main__


ROOT = Path(__file__).resolve().parents[1]


def locate_tool(name: str, explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit).expanduser().resolve()
    else:
        discovered = shutil.which(name)
        path = Path(discovered).resolve() if discovered else Path(name)
    if not path.is_file():
        raise SystemExit(f"找不到 {name}，请通过 --{name} 指定可执行文件。")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="构建无需 Python 和 FFmpeg 的 PickerRoy 独立应用")
    parser.add_argument("--ffmpeg")
    parser.add_argument("--ffprobe")
    parser.add_argument("--dist", default=str(ROOT / "dist"))
    parser.add_argument("--work", default=str(ROOT / "build"))
    args = parser.parse_args()

    ffmpeg = locate_tool("ffmpeg", args.ffmpeg)
    ffprobe = locate_tool("ffprobe", args.ffprobe)
    system = platform.system()
    icon = ROOT / "assets" / ("PickerRoy.ico" if system == "Windows" else "PickerRoy.icns")
    if not icon.is_file():
        icon = ROOT / "assets" / "PickerRoy-logo.png"

    options = [
        str(ROOT / "scripts" / "pickerroy_entry.py"),
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        "--name=PickerRoy",
        f"--paths={ROOT / 'src'}",
        f"--distpath={Path(args.dist).resolve()}",
        f"--workpath={Path(args.work).resolve()}",
        f"--specpath={ROOT / 'packaging'}",
        f"--icon={icon}",
        f"--add-data={ROOT / 'assets' / 'PickerRoy-logo.png'}{os.pathsep}assets",
        f"--add-data={ROOT / 'models' / 'intrinsic_popularity_resnet50.onnx'}{os.pathsep}models",
        f"--add-data={ROOT / 'THIRD_PARTY_NOTICES.md'}{os.pathsep}.",
        f"--add-data={ROOT / 'licenses'}{os.pathsep}licenses",
        f"--add-binary={ffmpeg}{os.pathsep}bin",
        f"--add-binary={ffprobe}{os.pathsep}bin",
        "--collect-data=cv2",
        "--collect-submodules=scenedetect",
    ]
    if system == "Darwin":
        options.extend(
            [
                "--osx-bundle-identifier=com.pickerroy.desktop",
                "--target-architecture=universal2" if platform.machine() == "universal2" else f"--target-architecture={platform.machine()}",
            ]
        )
    elif system == "Windows":
        version_file = ROOT / "packaging" / "windows-version.txt"
        options.append(f"--version-file={version_file}")
    PyInstaller.__main__.run(options)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
