# 下一版本 / Unreleased

本页记录 v0.3.4 之后的开发，未包含在 v0.3.4 下载包中。已发布标签和安装包不覆盖。/ These changes follow v0.3.4 and are not included in its downloads. Published tags and packages are preserved.

## 侧栏状态同步 / Sidebar state synchronization

修复辅助操作或程序设置按钮勾选状态时，侧栏高亮改变但正文仍停留在原页的问题。页面主动切换也会同步侧栏。/ Fix navigation that changed only the sidebar selection when activated through checked-state changes. Programmatic page changes now update the sidebar too.

回归测试覆盖辅助勾选路径、程序切页和普通点击且仅触发一次页面变化。原代码下新测试失败；2026-09-15 修复后真实 Mac 上全套 32 项测试通过。此检查不等于完成 VoiceOver 人工验收。/ Regression coverage checks state-based activation, programmatic navigation, and ordinary clicks with a single page-change emission. The added test failed before the fix; all 32 tests passed on a physical Mac after the fix on 2026-09-15. This does not replace a manual VoiceOver audit.

本次不改识别模型、候选排序、用户偏好库或已发布包。/ No recognition model, ranking logic, user preference store, or released package is changed.
