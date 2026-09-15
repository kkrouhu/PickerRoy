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
- 系统桌面分层 `.icon` 尚未完成：Icon Composer 首次使用协议待账户持有人亲自确认。设计示意不当作真实系统截图。/ Layered home-screen `.icon` is pending owner acceptance of the first-launch Icon Composer agreement. Design illustrations are not system screenshots.

本次品牌更新尚不在 v0.3.4 ZIP 中。源文件与复现方法见 `scripts/brand/README.md`。/ These brand changes are not in v0.3.4 downloads. See `scripts/brand/README.md` for sources and reproduction.
