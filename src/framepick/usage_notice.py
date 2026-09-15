"""Versioned, local-only acknowledgement of the material-use notice."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

NOTICE_VERSION = "2026-09-15.1"
NOTICE_TITLE = "素材与使用须知"
NOTICE_PARAGRAPHS = (
    "请仅使用你有权处理的素材，并自行确认截图及发布所需的版权、肖像和隐私授权。",
    "违法或侵权使用，由使用者依法承担相应责任。PickerRoy 不授予任何素材使用权。",
    "视频选帧、画面增强和偏好学习在本机完成。本须知不排除法律规定不得免除的责任。",
)


class UsageNoticeStore:
    def __init__(self, directory: Path):
        self.path = directory / "usage-notice.json"

    def acknowledged(self) -> bool:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return (isinstance(value, dict) and value.get("version") == NOTICE_VERSION
                    and value.get("acknowledged") is True)
        except (OSError, ValueError):
            return False

    def acknowledge(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        value = {"version": NOTICE_VERSION, "acknowledged": True,
                 "acknowledged_at": datetime.now(timezone.utc).isoformat()}
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(self.path)
