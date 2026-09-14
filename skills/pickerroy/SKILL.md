---
name: pickerroy
description: Install, launch, use, test, or troubleshoot the PickerRoy local video still-frame selection app on macOS and Windows. Use when a user mentions PickerRoy, wants to turn videos into ranked still images, asks about its aspect ratios or preference training, needs help choosing a release download, or reports that PickerRoy will not open, import, analyze, or export.
---

# PickerRoy

Treat PickerRoy as a standalone desktop application. The downloaded macOS or Windows app runs without Codex, Python, or a separate FFmpeg installation. This skill only gives Codex repeatable knowledge for helping with the app; installing the skill does not install the desktop app.

## Help the user

1. Identify macOS Apple Silicon, macOS Intel, or Windows x64 before choosing a release asset.
2. Prefer the matching ZIP from the repository's GitHub Releases page. Keep the entire extracted Windows folder together.
3. Explain the shortest usable flow: launch → confirm the green environment check → import → select aspect ratio → analyze → keep/favorite → export.
4. Keep instructions in Chinese unless the user requests another language.
5. If the user reports a failure, first inspect the Settings page's environment check and the log opened by “打开运行日志”. Preserve the original video and local preference database.
6. Never upload a user's videos, previews, exports, logs, or preference database without explicit permission.

Read [references/USAGE.md](references/USAGE.md) for installation, feature behavior, release naming, diagnosis, and developer verification commands.

## Accuracy boundaries

- Describe “热门视觉” as a relative score within the current video, produced locally by the bundled IIPA Instagram popularity model. Do not present it as a guaranteed like count.
- Describe A/B preference learning as local, incremental personalization that affects the next analysis. Do not claim continuous online training or scraping.
- Explain that technical rejection removes obvious unusable frames before aesthetic ranking, while the user remains the final editor.
- For HDR/BT.2020 material, tell the user to inspect exported color because this release does not apply an automatic creative grade.

## Repository work

When working inside the source repository, run the automated test suite before packaging. Build each operating-system package on its own operating system; PyInstaller is not a cross-compiler. Use the included release workflow for macOS Intel, macOS Apple Silicon, and Windows x64.
