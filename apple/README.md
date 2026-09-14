# PickerRoy Apple

PickerRoy 的原生 Apple 版本，共用一套 SwiftUI、AVFoundation、Vision 与 Core Image 代码，同时面向 iPhone、iPad 和 Mac。

## 设计目标

- 全程离线：视频解码、人物/风景分析、个性化学习和导出均在本机完成。
- 不收集数据：没有账号、服务器、广告 SDK 或分析 SDK。
- 适配 App Store：使用系统媒体框架，不捆绑 FFmpeg；Mac 目标启用 App Sandbox。
- 共用体验：导入确认、画幅选择、暂停、继续、取消、直接导出与优化后导出保持一致。

## 当前状态

这是 App Store 版本的可编译基础工程。提交 2026 年 App Store 前，需要在最新版 Xcode 26 或更高版本中设置开发团队、Bundle ID、签名与商店资料。

详细清单见 `../docs/app-store/APPLE_STORE_LAUNCH_CHECKLIST_zh-CN.md`。
