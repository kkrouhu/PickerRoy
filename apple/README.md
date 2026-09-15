# PickerRoy Apple

PickerRoy 的原生 Apple 版本，共用一套 SwiftUI、AVFoundation、Vision 与 Core Image 代码。当前先完成 Apple 芯片 Mac 的免费测试与 Mac App Store 发行，再推进 iPhone；暂不开发 iPad、Apple Watch 或 Vision Pro 版本。GitHub 桌面发行继续提供 Apple Silicon、Intel Mac 与 Windows x64 包。

## 设计目标

- 全程离线：视频解码、人物/风景分析、个性化学习和导出均在本机完成。
- 不收集数据：没有账号、服务器、广告 SDK 或分析 SDK。
- 适配 App Store：使用系统媒体框架，不捆绑 FFmpeg；Mac 目标启用 App Sandbox。
- 共用体验：导入确认、画幅选择、暂停、继续、取消、直接导出与优化后导出保持一致；iPhone 使用仅添加权限把结果保存到照片图库。
- V1.0 完全免费：不含 StoreKit、IAP、订阅、付费墙、购买入口或功能锁。
- 未来兼容：只有一个轻量 `FeatureAccessPolicy` 边界，商业化未启用，早期用户迁移政策未写死。

## 当前状态

这是 App Store 版本的可编译基础工程，已使用 Xcode 27 完成 macOS 与 iOS Release 无签名构建。正式提交前仍需设置开发团队、确认 Bundle ID、在真机完成飞行模式/相册/性能测试并上传商店资料。

详细清单见 `../docs/app-store/APPLE_STORE_LAUNCH_CHECKLIST_zh-CN.md`。

免费真机测试见 [Mac 与 iPhone 免费试用指引](../docs/FREE_TRIAL_GUIDE_zh-EN.md)。Xcode Personal Team 不是付费会员；个人签名需定期重新安装，不等同于 TestFlight 或公开发行。
