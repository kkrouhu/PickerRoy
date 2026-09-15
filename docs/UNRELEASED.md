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

## 原生截图一致性与文件保护 / Native frame fidelity and file protection

- 候选保留解码器返回的精确画面时间和分析时画幅。导出同一帧、同一裁切，之后改变画幅只影响新分析；无法精确还原时明确报错。/ Each candidate retains its decoded presentation time and analysis crop. Export reuses both, independent of later settings, and reports an error if that exact frame cannot be recovered.
- 同名视频增加来源标识；已存在的文件绝不覆盖，重复导出递增文件名。/ Source identifiers distinguish same-name videos. Exclusive writes and collision suffixes preserve existing exports and unrelated files.
- 分析和导出互斥，任务句柄分离；忙碌时锁定移除操作，导出时锁定勾选；迟到进度按操作标识过滤。单批次重复导入也会去重。/ Analysis and export are mutually exclusive with separate task handles. Removal is blocked while busy, selection is frozen during export, and operation IDs filter stale progress. Duplicate URLs within an import batch are also removed.
- 网格缩略图等比显示，不将不同画幅拉伸到统一比例。/ Grid thumbnails fit proportionally instead of stretching different crops to one ratio.

2026-09-15 验证：Mac/iPhone Release 无签名构建通过；合成 29.97 fps 视频的 5 组引擎检查通过（精确时间、画幅、同名与重复导出、并发防覆盖、优化 JPEG）；隔离偏好目录的 9 组模型 smoke 检查通过。合成检查不证明真实审美准确率，模型 smoke 不覆盖迟到回调或相册权限；界面与真机验收仍待完成。/ Validation: both unsigned Release builds passed, as did five generated-media engine checks and nine isolated model smoke groups. Synthetic checks do not measure aesthetic accuracy. Model smoke does not cover late callbacks or Photos authorization; UI and physical-device acceptance remain pending.

复现 / Reproduce:

```sh
bash scripts/check_native_export_fidelity.sh
bash scripts/apple-model-smoke/run.sh
```

系统媒体服务检查需要正常本机编解码权限；测试只使用合成数据，不访问用户视频或偏好。以上改动不在 v0.3.4 安装包中；原生“再筛一次”仍待接入，不能把已存在于旧原型的功能当成本工程已完成。/ Media checks require normal local codec access and use generated data only. These changes are not in v0.3.4 packages. Native “Select again” integration remains pending; the older prototype's implementation is not a completed feature in this target.
