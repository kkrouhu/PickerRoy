# v0.3.3 验证记录 / Verification record

## 已验证 / Verified

- 2026-09-15：29 项 Python 自动测试通过，0 失败。包括 Apple Vision 原生参数桥接、新标题、品牌图像存在性、界面初始化，以及现有视频分析、导出与偏好学习回归。/ 29 Python tests passed with no failures, covering native Apple Vision options bridging, the new headline, brand image availability, GUI initialization, and existing analysis, export, and preference behavior.
- 新版桌面导入界面以应用实际代码渲染，未使用用户视频。/ The refreshed desktop import screen was rendered from the application code without user footage.
- 最终 Apple 芯片 Mac 独立应用完成视频分析，生成 4 张推荐，直接 PNG 与优化 JPEG 均成功导出；实际分类后端为 `apple-vision`。/ The final Apple Silicon Mac standalone app analyzed a test video, recommended four frames, and exported direct PNG and enhanced JPEG successfully. Its actual classification backend was `apple-vision`.
- Mac 包内版本为 0.3.3；`codesign --verify --deep --strict` 通过。这仅验证临时本地签名的完整性，不是 Developer ID 或公证。/ Bundle version is 0.3.3 and strict ad-hoc signature verification passed; this is not Developer ID signing or notarization.
- 原生 Apple 工程完成 macOS Release 与 iPhone Release 无签名编译；iOS 设备家族限定为 iPhone，并关闭 iOS 版在 Mac / Vision 的兼容分发开关。编译通过不等同于真机安装成功。/ Native Apple macOS and iPhone Release builds compiled without signing. The iOS target is iPhone-only, with Mac/Vision compatibility distribution disabled. Compilation does not establish successful physical-device installation.

## 验证边界 / Limits

本版未更换识别模型或排序算法，没有用新测试集证明准确率、速度或审美质量提升。/ No recognition model or ranking algorithm changed, and no new benchmark establishes improved accuracy, speed, or aesthetic quality.

GitHub Actions 为各平台分别构建并运行独立包自检；以对应 workflow 的最终结果为准。/ GitHub Actions builds each platform and runs standalone smoke tests; consult the completed workflow for each platform's final result.

Developer ID 公证、Windows 商业签名、iPhone 真机验证和 App Store 审核未完成。/ Developer ID notarization, commercial Windows signing, physical iPhone validation, and App Store review remain incomplete.
