# PickerRoy 免费试用指引 / Free trial guide

更新于 2026-09-15 · 当前先 Mac，后 iPhone。无需为了试用立即购买 Apple Developer Program。

## 一、先试用 Mac

1. 打开本仓库的 [Releases](https://github.com/kkrouhu/PickerRoy/releases)。进入最新版本，不要点绿色 Code 按钮下载源码。
2. 点开 Assets。M 系列芯片请选择 `PickerRoy-macOS-Apple-Silicon.zip`；Intel 芯片请选择 `PickerRoy-macOS-Intel.zip`。不知道芯片时，点屏幕左上角苹果菜单 → 关于本机。
3. 同时下载中文或中英双语 PDF 说明书。Codex Skill 是可选文件，不是应用安装包。
4. 如果旧版正在分析，先等它结束或取消，导出想保留的照片，再正常退出旧版。不要删除本地数据目录。
5. 双击 ZIP 解压，把 `PickerRoy.app` 拖入“应用程序”。已有同名应用时先保留旧版备份，再替换。
6. 双击 PickerRoy。独立包包含视频引擎和模型，不需要 Python、Xcode 或 Codex。
7. 本测试包尚未获得 Developer ID 签名和 Apple 公证。若系统说无法验证开发者，先确认下载源和 SHA-256；确认可信后，再查看“系统设置 → 隐私与安全性”中本应用的“仍要打开”。若提示损坏或恶意软件，停止并反馈原文。不要关闭系统保护、移除隔离标记或执行网上的解锁命令。[Apple 官方安全说明](https://support.apple.com/en-us/102445)
8. 打开“设置”，查看运行环境自检；视频读取、视频信息识别与模型应可用。
9. 第一次选择一条已下载到本机的 10–30 秒短视频。点“添加视频”，确认导入成功，选画幅和模式，然后点“开始分析”。
10. 在结果中选“保留”或“收藏”，再点“导出已选画面”，选一个容易找到的新文件夹。先试“直接导出”，再试“优化后导出”；原视频不会被修改。
11. 用系统预览打开导出的图片，检查清晰度、裁切和色彩。记录你希望保留却没被选出的时间点；这些真实反馈比单纯反复运行更能帮助改进工具。

GitHub ZIP 是桌面测试版，不是已经通过审核的 App Store 版。公开下载是免费的；本版没有到期收费或自动付费入口。

## 二、iPhone 先尝试免费安装

手机不能直接打开 Mac ZIP。iPhone 原生工程需要由 Xcode 使用你的 Apple 账户签名后安装；暂不提供无需签名即可安装的 IPA。

1. 保持 Mac 上的 Xcode 已安装。用数据线连接 iPhone，解锁手机。
2. 如果手机显示“要信任此电脑吗”，由你本人确认并输入设备密码；电脑出现配对确认时按提示处理。
3. 在 Mac 打开 Xcode → Settings → Apple Accounts。已有账户可直接检查 Personal Team；没有则点 Sign In，自己输入 Apple 账户、密码和验证码，不要把这些信息发到聊天里。
4. 如果出现 Apple 协议，先阅读并由账户持有人确认。免费 Personal Team 与付费 Program 不是一回事；此时不需要点 Enroll、Subscribe 或购买会员。
5. 打开仓库中的 `apple/PickerRoyApple.xcodeproj`，选择 PickerRoy target → Signing & Capabilities，启用自动签名并选 Personal Team。实际个人 Team ID 不应提交到公开仓库。
6. 在顶部运行设备列表选择已连接的 iPhone。若签名提示 Bundle ID 冲突，先记录错误，由开发者处理唯一标识；不要随意删除旧 App 或吊销证书。
7. 如果 Xcode 提示需要 Developer Mode，由你在 iPhone“设置 → 隐私与安全性 → 开发者模式”中按系统指引开启、重启并确认。这是开发安装要求，会改变设备的安全设置，不会代替你暗中开启。
8. 点 Xcode 左上角运行按钮。等待构建、签名和安装。遇到钥匙串密码、设备密码、验证码或协议时由你完成；不要绕过系统校验。
9. 若系统要求信任开发者，在“设置 → 通用 → VPN 与设备管理”核对自己的开发者身份后按提示确认。
10. 手机出现 PickerRoy 后，先选一段存于“文件”的本地视频；确认导入、分析、选择、保存照片完整走通。只在保存时按需要允许添加照片。
11. 再做飞行模式测试和一条自己的常用视频测试，记录发热、等待时间、照片质量与失败提示。不读取整个图库，不上传测试视频。

免费 Personal Team 的安装描述文件有效期为 7 天，到期后需要通过 Xcode 重新构建安装；这不是 PickerRoy 收费倒计时。两台手机分别安装，能否完成以实际签名与设备状态为准。[Apple 免费个人团队说明](https://developer.apple.com/help/account/basics/about-your-developer-account)

## 三、什么时候才付费

先确认 Mac 和 iPhone 试用体验。准备向 App Store 分发时，再进行 Apple Developer Program 注册、身份核验、协议与付款。会员通常为每年 99 美元或本地等值金额，最终以 Apple 账户地区的结账页面为准；通过 Developer App 购买通常为自动续订年费。付费前单独核对金额、续订方式和个人/组织身份；个人注册的法定姓名会成为公开供应商名称。不会代替你付款。[Apple 注册说明](https://developer.apple.com/programs/enroll/) · [Developer App 注册与续订](https://developer.apple.com/help/account/membership/enrolling-in-the-app)

## English quick start

### Mac

1. Open this repository's Releases page and download the Apple Silicon or Intel ZIP that matches your Mac. Do not download the source archive or optional Codex Skill instead of the app.
2. Finish exports and quit any older version. Keep a backup, unzip, and move `PickerRoy.app` to Applications.
3. Open the app. Python, Xcode, and Codex are not required. This test build is not Developer ID-signed or notarized. Verify the source and checksum before considering the app-specific Open Anyway option. Stop on damage or malware warnings; never disable system protections.
4. Check Settings, import a short local video, choose an aspect ratio and mode, then start analysis.
5. Keep or favorite frames, export to a new local folder, and inspect the files in Preview. Record missed timestamps and unwanted selections for useful feedback.

### iPhone

The Mac ZIP does not install on iPhone. Open the native project in Xcode, sign in with your own Apple Account, select your Personal Team and connected iPhone, then build and run. Complete device trust, Developer Mode, passwords, verification codes, and agreements yourself when prompted. No paid membership is needed just to attempt personal-device testing. Free provisioning expires after seven days and requires rebuilding/reinstalling; it is not an app billing deadline. Test importing a local video, analysis, and saving selected images, then repeat offline. Installation remains subject to actual signing and device readiness.

### Payment and scope

Trial first, paid developer enrollment only when preparing distribution. Apple Silicon Mac is the first store target; iPhone follows. iPad, Apple Watch, and Vision Pro are not current targets. GitHub also carries Intel Mac and Windows x64 builds. Developer Program pricing and renewal follow Apple's checkout, not a fee charged by PickerRoy. No payment or agreement will be accepted on the owner's behalf.
