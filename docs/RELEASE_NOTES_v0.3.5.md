# PickerRoy v0.3.5 · 更自然的导出，更清楚的个性化 / Natural enhancement, clearer personalization

状态 / Status: **本地 Apple 芯片 Mac 测试包已验证；各平台公开资产以 Releases 为准。尚未上架 App Store。 / Local Apple Silicon Mac test package verified; public assets depend on Releases. Not published on the App Store.**

以下为 v0.3.5 的已实现更新，不是 v0.3.4 的功能说明。工程验证不等于审美准确率保证、法务审查或商店审批。/ These are implemented v0.3.5 changes, not v0.3.4 features. Engineering verification is not a guarantee of aesthetic accuracy, legal review, or store approval.

## 中文

### 增强画质，先照顾画面本身

保留原有“直接导出”。另一个导出选项统一为四个字：**增强画质**，界面不增加算法说明。

新的增强方向不再插值放大，也不对全部图片固定加锐化。在同一裁切下保持相同像素宽高，根据画面状态适度整理对比、可用的暗部层次和偏淡的色彩；只有适合的画面才做微量锐化。噪点明显、严重失焦、已足够锐利或色彩已经饱满的画面，需要克制处理。

这项 PickerRoy 特色功能追求自然的画面呈现，不宣传分辨率或清晰度提高，不生成原视频中没有的真实细节，也不声称行业独有。增强需要额外处理时间；原片已合适时变化可能很小，效果不保证适合每张图片。

已用桌面导出链路制作并检查 6 组真实户外同帧、同裁切、同尺寸对比，均为 3840 × 2880，锐化为零。本机单张直接导出约 0.60–0.72 秒，增强约 2.04–2.23 秒；仅代表本次样片与设备。完整图文附录、12 张全尺寸 PNG 和 3 张宣传候选保存在本地。公共三份手册说明功能与边界，不含尚未确认公开授权的私人视频抽帧。商店候选还须用最终 Apple 原生版和授权素材复验。

### 越选，越懂你的眼光

把本机个性化作为核心功能讲清楚：PickerRoy 从真实选择建立相对偏好，用于后续分析，而不是重新训练通用大模型，也不是导入次数越多就自动变聪明。

桌面版“收藏”同时选中导出，并表达高于普通“保留”的偏好。有效比较中，收藏高于保留，保留高于淘汰；没有可比较候选时，一次收藏不保证新增学习对。收藏不是自动保存图片、云同步或独立永久图库。

学习面板的样本、选择次数和偏好记录不应被称为准确率，也不设“达到固定数量就已经懂你”的承诺。桌面成对排序实现与 Apple 原生偏好实现分别验证，不混用功能名称与证据。

修复旧记录挤掉新选择、同一 A/B 反选产生相反重复信号、清除标签被重新推断为中性选择的问题。最多 800 组训练样本优先近期活动，并轮流参考不同视频与反馈类型，原历史不删除。候选 ID 加入精确时间与裁切标识，防止改采样模式后将旧偏好错配到新时刻；旧卡片标记不猜测迁移。

重复导出自动编号，不覆盖旧照片；失败清理本次临时文件，直接导出画面处理保持不变。

### 品牌与说明

- 镂空 ROY 光圈标志进入新版打包检查，避免源码已改而安装包仍显示旧标志。Apple 原生 Liquid Glass 分层图标与桌面兼容图标分别验证。
- 更新中文、English 和中英双语说明书，补充收藏、增强、个性化与素材使用边界。
- App Store 中英文介绍突出“增强画质”和“本机个性化”，仍为候选稿，不代表已经上线或完成审核。
- 已接入首次导入素材须知与设置内回看入口。默认未勾选，取消不导入，仅本机记录版本和时间；不代表软件验证过版权，不作绝对免责承诺。

### 验证结果与剩余边界

1. 87 项桌面自动测试通过，涵盖增强、导出防覆盖、须知、两用户相反偏好、旧样本压力与采样时间标识。
2. 实际 Mac 包显示 0.3.5，内置 Apple Vision 与视频引擎可用，分析、直接 PNG 和增强 JPEG 成功。图标哈希与最终资产一致，ad-hoc 签名验证通过。
3. 实际界面确认首次未勾选、“继续导入”禁用；取消不导入，设置可只读回看。没有代替真实用户同意。
4. 原生 Mac universal 与 iPhone arm64 无签名构建成功；15 类增强、5 组导出、9 组模型及须知状态测试通过。
5. 尚待真实 iPhone 安装与授权流程、原生真实素材效果、HDR/广色域专项、法律审阅与 App Store 提交。当前无 Developer ID 公证。

## English

### Enhance: respond to the image

The existing Direct export option remains. The alternative is labeled **增强画质** in Chinese, with no algorithm explanation added to the export interface; English documentation calls it Enhance.

The redesigned path no longer enlarges cropped images through interpolation or sharpens every frame by a fixed amount. At the same crop it retains pixel dimensions, making restrained adjustments to contrast, usable shadow tones, and muted color. Only suitable images receive a small amount of sharpening. Noise, severe defocus, already sharp edges, and already vivid color call for restraint.

This PickerRoy feature focuses on natural presentation, not increased resolution or clarity. It does not invent missing real detail or claim industry exclusivity. Enhancement adds processing time, and suitable originals may change very little; not every image is guaranteed to look better.

Six real outdoor comparisons were produced through desktop export and visually checked: same frame, crop, 3840 × 2880 dimensions, and zero sharpening. On this Mac, Direct took about 0.60–0.72 seconds and Enhance 2.04–2.23 seconds per image, not a universal benchmark. The illustrated appendix, twelve full-size PNGs, and three promotional candidates remain local. Public manuals describe behavior without uncleared private frames. Store candidates require public-media permission and validation using the final native Apple build.

### A shortlist that learns your taste

Local personalization is a core feature: actual decisions create relative preferences for later analyses. This is not retraining a general-purpose AI model, and importing more footage alone does not make the tool learn a user's taste.

In the desktop version, Favorite both selects a frame for export and expresses a stronger preference than Keep. Usable comparisons rank Favorite above Keep, and Keep above Reject. An isolated Favorite without comparable candidates need not create a training pair. Favorite is not automatic file export, cloud sync, or a separate permanent photo library.

Learning examples, decision counts, and preference records are not accuracy scores. No fixed count guarantees the app has learned a user's taste. The desktop pairwise-ranking implementation and native Apple preference implementation must be verified separately; their controls and evidence are not interchangeable.

Corrects older records crowding out new feedback, opposing duplicate A/B decisions, and cleared labels being inferred as neutral choices. Up to 800 training pairs prioritize recent activity and alternate across videos and feedback types without deleting history. Time- and crop-specific candidate identities prevent changed sampling from attaching old feedback to a different moment; old card labels are not guessed onto new candidates. Repeated exports use numbered names instead of overwriting existing photos; failed attempts clean up their own temporary files.

### Identity and documentation

- Include the outlined ROY aperture mark in final-package checks so installed branding matches the source update. Validate native Liquid Glass and desktop-compatible icons separately.
- Update Chinese, English, and bilingual manuals with Favorite, Enhance, personalization, and media-rights guidance.
- Emphasize Enhance and on-device personalization in candidate App Store copy, without implying the app is already submitted or approved.
- A first-import notice and Settings review entry are implemented. The checkbox starts clear; cancellation does not import. Only version and time are recorded locally. The notice does not verify copyright ownership or claim blanket immunity.

### Validation and remaining boundaries

1. 87 desktop automated tests passed, including enhancement, non-overwrite export, notice flow, opposite-user preferences, historical sample pressure, and time-specific identities.
2. Actual Mac package shows 0.3.5 and uses bundled engines and Apple Vision. Analysis, Direct PNG, Enhance JPEG, icon hashes, and ad-hoc signature checks passed.
3. Actual UI verified the unchecked first notice, disabled continuation, cancellation without import, and read-only access. No real-user agreement was accepted by the test operator.
4. Native Mac universal and iPhone arm64 unsigned builds passed, together with 15 enhancement categories, 5 fidelity groups, 9 model groups, and notice state checks.
5. Physical-iPhone installation and permissions, native real-footage acceptance, HDR/wide-color testing, legal review, and App Store submission remain pending. No Developer ID notarization.
