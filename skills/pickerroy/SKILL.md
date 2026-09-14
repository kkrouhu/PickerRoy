---
name: pickerroy
description: Install, launch, use, personalize, test, troubleshoot, or safely improve the PickerRoy local video still-frame selection app on macOS and Windows. Use when a user mentions PickerRoy, wants ranked still images, asks about local preference learning, wants Codex to interpret a PickerRoy preference database or tune the source for a shooting style, needs a release download, or reports an import, analysis, pause, cancel, or export failure.
---

# PickerRoy

Treat PickerRoy as a standalone desktop application. The downloaded macOS or Windows app runs without Codex, Python, or a separate FFmpeg installation. This skill only gives Codex repeatable knowledge for helping with the app; installing the skill does not install the desktop app.

## Help the user

1. Identify macOS Apple Silicon, macOS Intel, or Windows x64 before choosing a release asset.
2. Prefer the matching ZIP from the repository's GitHub Releases page. Keep the entire extracted Windows folder together.
3. Explain the shortest usable flow: launch → confirm the green environment check → import → select aspect ratio → analyze (pause/resume/cancel when needed) → keep/favorite/reject → direct or optimized export.
4. Keep instructions in Chinese unless the user requests another language.
5. If the user reports a failure, first inspect the Settings page's environment check and the log opened by “打开运行日志”. Preserve the original video and local preference database.
6. Never upload a user's videos, previews, exports, logs, or preference database without explicit permission.

Read [references/USAGE.md](references/USAGE.md) for installation, feature behavior, personalization modes, release naming, diagnosis, and developer verification commands.

## Personalization and deeper improvement

The app adapts automatically without Codex: Keep, Favorite, Reject, and A/B choices become local pairwise training signals and affect later analyses. Re-running the same video without making choices is not training.

When the user wants to inspect what PickerRoy learned, run `scripts/profile_preferences.py` against the `pickerroy.sqlite3` path shown on the app's Settings page. Share the generated summary, not the database, videos, or previews, unless the user explicitly authorizes those files.

When the user wants a source-level improvement beyond built-in personalization:

1. Use the preference summary plus a small, user-authorized evaluation set to identify a concrete failure pattern.
2. Preserve the personal database and original videos. Keep private media, caches, databases, logs, and tokens out of Git.
3. Change the narrowest relevant features, weights, sampling, or UI behavior; add a meaningful test and run the full suite.
4. Build packages only when the user asks. Publishing a release or replacing GitHub assets is a separate external mutation and needs explicit authorization.
5. State whether a change is heuristic tuning, local preference learning, or genuine model training. Never call unlabelled repeated analysis “training.”

## Accuracy boundaries

- Describe “热门视觉” as a relative score within the current video, produced locally by the bundled IIPA Instagram popularity model. Do not present it as a guaranteed like count.
- Describe Keep/Favorite/Reject and A/B preference learning as local, incremental personalization that affects the next analysis. Do not claim continuous online training or scraping.
- Describe optimized export as high-quality resizing plus restrained tone, color, and sharpness enhancement. It cannot recreate detail absent from the source.
- Explain that technical rejection removes obvious unusable frames before aesthetic ranking, while the user remains the final editor.
- For HDR/BT.2020 material, tell the user to inspect exported color because this release does not apply an automatic creative grade.

## Repository work

When working inside the source repository, run the automated test suite before packaging. Build each operating-system package on its own operating system; PyInstaller is not a cross-compiler. Use the included release workflow for macOS Intel, macOS Apple Silicon, and Windows x64.
