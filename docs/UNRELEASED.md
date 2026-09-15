# 下一版本 / Unreleased

本页记录 v0.3.4 之后的开发，未包含在 v0.3.4 下载包中。已发布标签和安装包不覆盖。/ These changes follow v0.3.4 and are not included in its downloads. Published tags and packages are preserved.

## 侧栏状态同步 / Sidebar state synchronization

修复辅助操作或程序设置按钮勾选状态时，侧栏高亮改变但正文仍停留在原页的问题。页面主动切换也会同步侧栏。/ Fix navigation that changed only the sidebar selection when activated through checked-state changes. Programmatic page changes now update the sidebar too.

回归测试覆盖辅助勾选路径、程序切页和普通点击且仅触发一次页面变化。原代码下新测试失败；2026-09-15 修复后真实 Mac 上全套 32 项测试通过。此检查不等于完成 VoiceOver 人工验收。/ Regression coverage checks state-based activation, programmatic navigation, and ordinary clicks with a single page-change emission. The added test failed before the fix; all 32 tests passed on a physical Mac after the fix on 2026-09-15. This does not replace a manual VoiceOver audit.

本次不改识别模型、候选排序、用户偏好库或已发布包。/ No recognition model, ranking logic, user preference store, or released package is changed.

## 镂空光圈与玻璃背景 / Outline iris and glass enclosure

- 保留 R/Y 字形，O 从实心叶片改为六片光圈线框，中心与叶片留白。提供透明前景和兼容图标。/ Preserve the R/Y lettering, replacing solid iris blades with an outlined aperture and transparent interiors. Add separate foreground and fallback assets.
- Apple 原生 App 内标志：iOS/macOS 26+ 使用系统 Liquid Glass；浅深色字标自适应，降低透明度或旧系统回退实色底。/ The in-app Apple mark uses Liquid Glass on iOS/macOS 26+, adaptive foreground color, and an opaque fallback for older systems or Reduce Transparency.
- macOS 与 iPhone Release 无签名构建通过；真实设备外观/辅助功能仍待验收。/ Unsigned macOS and iPhone Release builds passed; device appearance and accessibility remain to be reviewed.
- 系统桌面分层 `AppIcon.icon` 已创建并接入 Apple 原生工程。浅色保留黑字，深色和单色配置独立白色前景；玻璃材质集中于底层，细光圈不增加折射。/ The layered `AppIcon.icon` is integrated into the Apple target. Default uses black lettering; dark and mono use explicit white foregrounds. Glass treatment stays in the enclosure to preserve the fine iris outline.
- 使用 Apple 官方渲染器导出 iOS 26 的默认、深色、着色和透明外观，另检查 64px 小图。它们是图标渲染预览，不是手机安装截图；真机壁纸与系统显示仍待验收。见[实际渲染预览](brand-preview/README.md)。/ Apple-rendered iOS 26 default, dark, tinted, and clear previews plus 64px checks are available. These are icon renders, not screenshots of an installed app; physical-device and wallpaper review is pending. See [rendered previews](brand-preview/README.md).
- 原静态 AppIcon 目录完整保留到 `apple/CompatibilityAssets`，不与分层图标同时编译；最低系统要求和仅 iPhone 的设备范围不变。/ The static icon catalog is preserved in `apple/CompatibilityAssets`, outside compilation. Minimum OS versions and the iPhone-only device family are unchanged.
- 最终源文件重新构建：Mac/iPhone Release 无签名构建通过，34 项本机测试通过（包括 Apple Vision 和两项图标完整性测试）。限制沙箱中 Vision 无法创建系统图像缓冲区；在本机正常权限下复测通过，没有为此放宽或跳过测试。/ Final Mac/iPhone unsigned Release builds and all 34 local tests passed, including Apple Vision and two icon integrity checks. Vision could not allocate a system image buffer in the restricted sandbox, then passed with normal local permissions; no test was weakened or skipped for that failure.

本次品牌更新尚不在 v0.3.4 ZIP 中。源文件与复现方法见 `scripts/brand/README.md`。/ These brand changes are not in v0.3.4 downloads. See `scripts/brand/README.md` for sources and reproduction.
