# Static icon compatibility archive / 静态图标兼容存档

`AppIcon.appiconset` retains the complete static icon set previously compiled by
the native project. This directory is deliberately **not** an Xcode resource or
asset catalog input. No static image was deleted during the layered-icon migration.

原生工程现在使用 `PickerRoyApple/AppIcon.icon`。Xcode 会从分层图标生成旧版系统所需
的图像；这里保留原先的完整静态图标，方便旧工具链、回退和设计对照，不参与当前构建。
不要把这个目录重新加入原生工程的 Resources。

`scripts/update_brand_formats.py` updates the compatibility set here. It must not
recreate `PickerRoyApple/Assets.xcassets/AppIcon.appiconset`, which would introduce
a competing icon source. The Python desktop package continues to use
`assets/PickerRoy.icns` (Mac) and `assets/PickerRoy.ico` (Windows).

Selecting the layered icon does not change the deployment targets (iOS 17 and
macOS 14), and it does not change the already-published v0.3.4 package. The in-app
`BrandForeground` and `BrandMark` image sets remain in the compiled asset catalog.

Reference: [Apple Icon Composer integration](https://developer.apple.com/documentation/xcode/creating-your-app-icon-using-icon-composer).
