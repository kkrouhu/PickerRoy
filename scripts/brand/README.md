# ROY brand sources

The original R/Y outlines and six-blade photographic aperture are generated from `RoyBrand.swift`. The aperture now contains black outlines and transparent blade interiors, retaining the original center and silhouette. Small raster exports use a slightly heavier stroke for legibility.

## Rendering

On a Mac with Xcode installed, from the repository root:

```sh
mkdir -p work/brand-stage work/swift-module-cache
xcrun swiftc -module-cache-path work/swift-module-cache scripts/brand/RoyBrand.swift scripts/brand/RenderBrand.swift -o work/render-brand
work/render-brand work/brand-stage .
python scripts/update_brand_formats.py
iconutil -c icns work/PickerRoy.iconset -o assets/PickerRoy.icns
cp assets/PickerRoy-logo.png apple/PickerRoyApple/Assets.xcassets/BrandMark.imageset/BrandMark.png
```

`assets/PickerRoy-foreground.png` is transparent, for layered icon preparation. `BrandForeground.imageset` has a slightly stronger small-size stroke and template rendering for in-app light/dark adaptation. Existing opaque PNG/ICNS/ICO exports remain compatibility assets; they are not finished Liquid Glass `.icon` files.

`RenderGlassPreview.swift` draws a labelled **static design illustration** with gradients. It is not an Icon Composer export, actual SpringBoard screenshot, or proof of native material rendering. SwiftUI ImageRenderer did not render the native glass badge reliably, so the illustration does not claim to capture that effect.

## Native treatment

The Apple target uses `glassEffect` only on the logo enclosure on iOS/macOS 26 and later. The foreground stays crisp and uses the system primary color. Older systems and Reduce Transparency use an opaque enclosure. No interactive glass behavior is attached to this decorative, non-button mark.

Home-screen icon layers, Default/Dark/Mono appearance, and actual device appearance still need Icon Composer and physical-device review. Its first-launch license agreement must be confirmed by the owner; no agreement was accepted by automation. Do not bypass the license gate through command-line tools.

Official references: [Icon Composer](https://developer.apple.com/icon-composer/), [SwiftUI Liquid Glass](https://developer.apple.com/documentation/swiftui/applying-liquid-glass-to-custom-views).
