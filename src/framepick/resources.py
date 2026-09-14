from __future__ import annotations

import sys
from pathlib import Path


def resource_candidates(relative: str | Path) -> list[Path]:
    """Return source and frozen-app locations for a bundled resource."""
    relative = Path(relative)
    candidates: list[Path] = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        bundle_root = Path(meipass)
        candidates.extend(
            [
                bundle_root / relative,
                bundle_root.parent / "Resources" / relative,
            ]
        )
    executable = Path(sys.executable).resolve()
    candidates.extend(
        [
            executable.parent / relative,
            executable.parent.parent / "Resources" / relative,
            Path(__file__).resolve().parents[2] / relative,
        ]
    )
    unique: list[Path] = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    return unique


def resource_path(relative: str | Path) -> Path:
    """Resolve a resource in development and in a PyInstaller bundle."""
    candidates = resource_candidates(relative)
    return next((path for path in candidates if path.exists()), candidates[-1])
