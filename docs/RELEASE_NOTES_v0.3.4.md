# PickerRoy v0.3.4 · 品牌、兼容性与免费试用 / Identity, compatibility, and free trial

## 中文

v0.3.4 延续 v0.3.3 的界面与功能，修正发布验证方式：GitHub 的部分 Apple 芯片虚拟机返回 Vision Code 9（无法创建推理环境），仅在该明确环境与错误条件下跳过真实硬件集成检查；另增加两个跨平台原生参数桥接测试，其他错误仍会使发布失败。真实 Mac 的 Vision 检查与独立包验证保留。v0.3.3 的首次自动发布未完成，标签与失败记录保留，不覆盖历史。

本次更新聚焦品牌识别、产品表达和发布资料，保留 v0.3.2 的视频处理、暂停/继续、队列、偏好学习与导出能力。

- 统一白底黑色 ROY 标志，以六叶光圈构成 O；调整字形、间距与视觉居中，并提供适配小尺寸的图标。
- 桌面应用侧栏加入新版品牌标志；Mac、Windows 图标与 Apple 原生工程的品牌资源同步更新。
- 主标题改为“从视频中精选好照片”，强调主动从视频筛选清晰、自然、适合使用的图片并保存到本地，不再使用“补救错过拍摄”的表达。
- 更新中文、English 和中英双语使用说明书，增加本版变化、安装/升级及隐私边界说明。
- 修正应用版本信息：Mac 应用包与 Windows 文件版本和 v0.3.4 保持一致。
- 修复较新 macOS 上 Apple Vision 参数桥接异常导致分类降级的问题；自检报告现在记录分析后实际使用的分类后端。
- 每版独立发布并保留历史版本；应用包和说明书提供 SHA-256，便于核验下载。
- 明确免费试用与上架顺序：Apple 芯片 Mac 优先，iPhone 随后；暂不支持 iPad、Apple Watch 或 Vision Pro。GitHub 保留 Intel Mac 与 Windows x64 下载。

本版没有更换筛选算法，也不宣称识别准确率或处理速度提高。视频、偏好数据与导出仍在本机处理；不加入账号、付费墙、追踪或上传服务。

这是 GitHub 桌面测试发行版，不是 App Store 发行。Mac 构建尚未使用 Developer ID 签名和 Apple 公证；首次打开可能触发系统安全确认。不要关闭系统安全保护。iPhone 真机测试及 App Store 提交单独进行。

## English

v0.3.4 preserves the v0.3.3 interface and features while correcting release validation. Some hosted Apple Silicon VMs return Vision Code 9 (no inference context); the hardware integration check is skipped only for that explicit hosted environment and error. Two cross-platform native-options contract tests were added; other errors still fail the build. Real-Mac Vision and standalone verification are retained. The first v0.3.3 automated release did not finish; its tag and failed run remain visible rather than rewriting history.

This update focuses on visual identity, product messaging, and release documentation. It preserves the video processing, pause/resume, queueing, local preference learning, and export features of v0.3.2.

- A consistent black ROY mark on white, with a six-blade aperture forming the O; refined letter shapes, spacing, optical centering, and small-size icon rendering.
- Updated desktop sidebar branding, Mac/Windows application icons, and brand assets in the native Apple project.
- New headline: “Select great photos from video.” The product is about intentionally creating useful photographs from video, not recovering missed photo opportunities.
- Updated Chinese, English, and bilingual manuals, including this release's changes, installation/upgrades, and privacy boundaries.
- macOS bundle and Windows file versions now match v0.3.4.
- Fixed an Apple Vision options-bridging error on newer macOS that could force classification to fall back. Smoke-test reports now record the backend actually used after analysis.
- Versioned releases preserve earlier downloads. Application archives and manuals include SHA-256 checksums.
- Clarified the free-trial and store roadmap: Apple Silicon Mac first, iPhone next; iPad, Apple Watch, and Vision Pro are out of scope. GitHub still includes Intel Mac and Windows x64 downloads.

No selection algorithm has changed in this release; no improved recognition accuracy or speed is claimed. Videos, preferences, and exports are processed locally. No accounts, paywalls, tracking, or upload service are added.

This is a GitHub desktop test release, not an App Store release. The Mac build is not Developer ID-signed or notarized by Apple, so first launch may require a system security confirmation. Do not disable system protections. Physical iPhone testing and App Store submission are separate steps.
