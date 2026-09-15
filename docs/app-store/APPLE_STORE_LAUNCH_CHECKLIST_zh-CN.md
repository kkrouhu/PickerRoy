# PickerRoy Apple Store 上架总清单

更新日期：2026-09-15

## 最终目标

先完成免费本地试用，再先上 Mac App Store（Apple 芯片优先），随后上 iPhone App Store；暂不考虑 iPad、Apple Watch 或 Vision Pro。GitHub 桌面包保留 Apple Silicon、Intel Mac 与 Windows x64。视频、图片、审美偏好和导出均在用户设备本地处理；没有账号、服务器、广告或行为追踪。

## 必须费用

| 项目 | 金额 | 是否分别收费 |
|---|---:|---|
| Apple Developer Program | 通常每年 99 美元或本地等值金额，以 Apple 结账页面为准 | 一份会员可用于 Mac 与 iPhone 分发 |
| Xcode、App Store Connect、TestFlight | ¥0 | 已包含 |
| 隐私政策与支持页面 | ¥0 | 使用 GitHub Pages，无需购买域名 |
| PickerRoy V1.0 | 计划免费提供当前核心功能 | 先 Mac，后 iPhone |

当前免费试用不需要先购买会员。通过 Developer App 购买的会员通常按年自动续订，准备上架时再核对当地价格和续订条款，由账户持有人付款。V1.0 计划免费，因此首发不需要配置消费者付款产品。

V1.0 不启用付费下载、IAP 或订阅。收款银行、付费税务和 Small Business Program 可以推迟到未来明确启用商业化时处理；开发者会员身份和 App Store Connect 协议仍需按 Apple 页面要求完成。

## 你本人需要准备

- 一个长期使用的 Apple 账户，开启双重认证。
- 与身份证件一致的法定姓名、出生日期、手机号和可收信地址。
- 中国大陆个人注册时，按 Apple Developer App 的提示完成人脸/证件验证。
- 在 Apple 账户付款方式中绑定一张可正常支付的银行卡；Apple 账户余额不能支付开发者会员费。
- 决定以“个人”还是“组织”身份发布：
  - 个人：流程更快，App Store 开发者名称显示本人法定姓名。
  - 组织：显示公司法定名称，需要法人主体、工作域名邮箱、公开官网、总部电话地址、签约权限和免费的 D-U-N-S 编号；验证通常更久。
- 一台能够安装最新版 Xcode 的 Mac。
- 至少一台真实 iPhone 用于最终性能、发热、存储和导出测试。
- 未来启用商业化时，再准备与个人开发者法定姓名一致的收款账户、Paid Apps Agreement、税务资料和 Small Business Program 申请。

## 我已经准备/正在准备

- 原生 SwiftUI 多平台工程。
- AVFoundation 本地视频解码，不上传视频。
- Vision 本地人物检测与画面分析。
- 本地偏好学习、暂停/继续/取消、画幅选择、直接/优化导出。
- Mac App Sandbox 权限文件。
- Privacy Manifest：不追踪、不收集数据。
- 中英文商店文案、隐私政策、支持页面、审核说明。
- App 图标与 App Store 演示图版式。

## 技术与提交阶段

1. 在 Xcode 26 或更新版本打开 `apple/PickerRoyApple.xcodeproj`。
2. 在 Signing & Capabilities 中选择你的开发团队。
3. 确认最终 Bundle ID。项目当前临时值是 `com.roy.pickerroy`，正式上传前应改成你控制且未被占用的标识。
4. 在 App Store Connect 只新建一条 PickerRoy App 记录，同时添加 iOS 与 macOS，两个平台使用相同 Bundle ID，形成通用购买。
5. 将 V1.0 定价设为免费，不创建任何 IAP、订阅或付费墙。
6. 收款银行、付费税务与未来商业化配置暂不启用；价格草案不代表最终批准价格。
7. 配置版本号、年龄分级、分类和全球可用地区。
8. 上传构建，先通过 TestFlight/本机测试。
9. 填写“App 不收集数据”、出口合规、内容版权、审核联系人和审核说明。
10. 上传截图、简介、隐私政策 URL、支持 URL。
11. 选择手动发布，提交审核。
12. 按审核反馈修正；获批后点击发布。获批后的商店生效仍可能需要最多约 24 小时。

## 一天内能做到什么

可以完成代码、编译、商店资料、演示图、开发者注册申请和首次 TestFlight/审核提交（前提是 Xcode、账号审核、付款和签名及时完成）。无法承诺一天内正式上架，因为会员身份核验、构建处理和 App Review 的时间由 Apple 控制。Apple 公布的总体数据是约 90% 的提交在 24 小时内得到审核结果，但这不是单个 App 的保证。

## 中国大陆与备案

离线处理可以显著减少服务器、网络安全、跨境传输和个人信息处理负担，也让 App 隐私申报更简单，但它不会自动免除 App Store 的地区合规要求。中国大陆商店是否需要提供 App 备案/ICP 信息，以 App Store Connect 对该 App 类别和账户主体的实际提示为准。

最快的商业路径是：先提交符合条件的全球地区；如果中国大陆区域要求额外备案而暂时未完成，可先不勾选中国大陆，备案完成后再增加该地区。最终是否这样发布，必须由账号持有人决定。

## 官方资料

- [Apple Developer Program 注册与付款](https://developer.apple.com/cn/help/account/membership/enrolling-in-the-app/)
- [App Review 审核概览](https://developer.apple.com/app-store/review/)
- [上传构建要求](https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds)
- [App 隐私信息](https://developer.apple.com/help/app-store-connect/manage-app-information/manage-app-privacy)
- [Mac App Sandbox](https://developer.apple.com/documentation/security/protecting-user-data-with-app-sandbox)
