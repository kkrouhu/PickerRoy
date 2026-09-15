# v0.3.4 验证记录 / Verification record

## 已验证 / Verified

- 2026-09-15：真实 Mac 上 31 项 Python 自动测试通过，0 失败。包括原生参数桥接的两个独立跨平台测试、Apple Vision 真实调用，以及界面、视频分析、导出与偏好回归。/ 31 Python tests passed on a physical Mac, including two independent cross-platform native-options contract cases, real Vision execution, UI, analysis, export, and preference regressions.
- 新版桌面导入界面以应用实际代码渲染，未使用用户视频。/ The refreshed desktop import screen was rendered from the application code without user footage.
- 最终 Apple 芯片 Mac 独立应用完成视频分析，生成 4 张推荐，直接 PNG 与优化 JPEG 均成功导出；实际分类后端为 `apple-vision`。/ The final Apple Silicon Mac standalone app analyzed a test video, recommended four frames, and exported direct PNG and enhanced JPEG successfully. Its actual classification backend was `apple-vision`.
- Mac 包内版本为 0.3.4；`codesign --verify --deep --strict` 通过。这仅验证临时本地签名的完整性，不是 Developer ID 或公证。/ Bundle version is 0.3.4 and strict ad-hoc signature verification passed; this is not Developer ID signing or notarization.
- 原生 Apple 工程完成 macOS Release 与 iPhone Release 无签名编译；iOS 设备家族限定为 iPhone，并关闭 iOS 版在 Mac / Vision 的兼容分发开关。编译通过不等同于真机安装成功。/ Native Apple macOS and iPhone Release builds compiled without signing. The iOS target is iPhone-only, with Mac/Vision compatibility distribution disabled. Compilation does not establish successful physical-device installation.

## 验证边界 / Limits

v0.3.3 首次发布的 Apple Silicon hosted runner 返回 `com.apple.Vision Code=9`，而 Intel 与 Windows 构建成功。v0.3.4 只在 GitHub Actions 且该明确错误时跳过真实硬件检查；桥接契约检查仍执行。此 skip 不算真实 Vision 推理通过，参见最终 Actions 的计数。/ The initial v0.3.3 Apple Silicon hosted runner returned Vision Code 9; Intel and Windows succeeded. v0.3.4 skips hardware integration only for that exact error in GitHub Actions, while keeping contract checks. A skip is not a passed real-Vision inference test; see the final Actions counts.

本版未更换识别模型或排序算法，没有用新测试集证明准确率、速度或审美质量提升。/ No recognition model or ranking algorithm changed, and no new benchmark establishes improved accuracy, speed, or aesthetic quality.

GitHub Actions 为各平台分别构建并运行独立包自检；以对应 workflow 的最终结果为准。/ GitHub Actions builds each platform and runs standalone smoke tests; consult the completed workflow for each platform's final result.

Developer ID 公证、Windows 商业签名、iPhone 真机验证和 App Store 审核未完成。/ Developer ID notarization, commercial Windows signing, physical iPhone validation, and App Store review remain incomplete.
