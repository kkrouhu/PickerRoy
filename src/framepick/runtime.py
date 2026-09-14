from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .classification import build_classifier
from .media import resolve_executable
from .popularity import default_model_path


@dataclass(frozen=True, slots=True)
class RuntimeCheck:
    label: str
    ready: bool
    detail: str


def _tool_check(label: str, name: str) -> RuntimeCheck:
    resolved = resolve_executable(name)
    path = Path(resolved)
    ready = path.is_file() and (os.name == "nt" or os.access(path, os.X_OK))
    return RuntimeCheck(label, ready, str(path) if ready else "未找到")


def runtime_checks() -> list[RuntimeCheck]:
    ffmpeg = _tool_check("视频读取与导出", "ffmpeg")
    ffprobe = _tool_check("视频信息识别", "ffprobe")
    model = default_model_path()
    model_check = RuntimeCheck(
        "热门视觉模型",
        model.is_file(),
        "本地模型已加载" if model.is_file() else "模型文件缺失，将使用基础排序",
    )
    try:
        classifier_name = build_classifier().active_name
        classifier_check = RuntimeCheck("内容分类", True, classifier_name)
    except Exception as exc:
        classifier_check = RuntimeCheck("内容分类", False, f"初始化失败：{exc}")
    return [ffmpeg, ffprobe, model_check, classifier_check]


def runtime_ready(checks: list[RuntimeCheck] | None = None) -> bool:
    rows = checks if checks is not None else runtime_checks()
    return all(row.ready for row in rows[:2])
