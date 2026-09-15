# 发布前权利与合规检查 / Pre-release rights and compliance

此文件是开发检查清单，不是法律意见，也不是法律审查已完成的证明。用户须知不能保证排除所有法律风险。

This is an engineering checklist, not legal advice or proof of legal review. A user notice cannot eliminate every legal risk.

## 已落实的产品边界 / Implemented boundaries

- 核心视频处理在本机进行；没有为收集视频、导出图片或偏好而建立的上传服务。
- 导入须知默认不勾选；取消不开始导入。后续可再次查看；须知改版后重新确认。
- 确认记录只存本地版本及时间；不表示开发者验证过素材版权、肖像许可或发布授权。
- 选帧和增强不授予素材使用权，也不宣传可绕过 DRM、去水印或下载受保护内容。
- 宣传真实增强效果与有限本机偏好学习；不作“行业独有”“每次必然更准确”“完全免责”等未证实承诺。

## 正式发布前仍需完成 / Still required before public launch

1. 请合格法律专业人士结合经营主体、面向地区和实际功能审阅用户条款、隐私政策及须知。不能用格式条款排除法定不可免除的责任。
2. 确认应用、第三方依赖、模型、字体和所有商店/说明书素材的分发许可。代码许可、模型许可和素材许可分别审查，不能相互替代。
3. 私人测试片可以用于本机测试；进入公开仓库、商店或推广前另行确认版权、可识别人物与地点等必要权利。不把本地测试授权视为公开发布授权。
4. 核验 App Store 隐私申报与实际发布二进制一致；如增加网络、分析、购买或云同步，先更新政策、申报与实现。
5. 保留各版须知正文与版本号；仅在本机保存确认，不能对外声称已有身份验证、完整审计证据或版权查验。
6. Mac 删除 App 不一定删除 Application Support 中的缓存和偏好；隐私说明必须准确描述数据删除方式。

Have qualified counsel review the operator, distribution regions, actual behavior, terms, and privacy disclosures before launch. Clear third-party licenses and public marketing-media rights separately. A local acknowledgment is neither identity verification nor a copyright audit, and deleting a Mac app may leave its local support data behind.

## 参考依据 / Primary references

- [《中华人民共和国民法典》](https://www.cac.gov.cn/2020-06/01/c_15925617772683192.htm)：第 496–497 条格式条款提示义务与效力；第 506 条不得免责的情形。
- [《中华人民共和国著作权法》](https://www.npc.gov.cn/c2/c30834/202011/t20201119_308796.html)：素材使用、复制与合理使用等边界，不存在“截图即可自由发布”的一般许可。
- [Apple App Review Guidelines, 5.2 Intellectual Property](https://developer.apple.com/app-store/review/guidelines/#intellectual-property)：应用内容与宣传素材的必要知识产权许可。
