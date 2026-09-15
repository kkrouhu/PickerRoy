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

`assets/PickerRoy-foreground.png` is transparent. It is also included in `apple/PickerRoyApple/AppIcon.icon/Assets`. `BrandForeground.imageset` has a slightly stronger small-size stroke and template rendering for in-app light/dark adaptation. Existing opaque PNG/ICNS/ICO exports remain compatibility assets, separate from the native layered icon. The old native catalog now lives in `apple/CompatibilityAssets`, outside the compiled asset catalog.

`RenderGlassPreview.swift` draws a labelled **static design illustration** with gradients. It is not an Icon Composer export, actual SpringBoard screenshot, or proof of native material rendering. SwiftUI ImageRenderer did not render the native glass badge reliably, so the illustration does not claim to capture that effect.

## Native treatment

The Apple target uses `glassEffect` only on the logo enclosure on iOS/macOS 26 and later. The foreground stays crisp and uses the system primary color. Older systems and Reduce Transparency use an opaque enclosure. No interactive glass behavior is attached to this decorative, non-button mark.

`AppIcon.icon` was created in Icon Composer after the owner explicitly confirmed its first-launch agreement. It uses the system-light enclosure, an un-refracted black foreground, and white overrides for Dark and Mono (the JSON appearance key is `tinted`). Automatic Mono initially obscured the lettering, so an explicit override preserves the reviewed shape. No watchOS support is selected. Mac and iPhone targets use this layered resource; Xcode generates legacy renditions for older supported systems.

Apple's rendered previews for design generation 26 are in [`docs/brand-preview`](../../docs/brand-preview/README.md). Device installation, wallpaper adaptation, and physical accessibility review remain pending. Preview exports are not evidence of App Store approval or installation.

To reproduce a preview, use the `ictool` bundled **inside Icon Composer**, not the different `xcrun ictool`. This command requires a functioning local graphics session and may not work in a restrictive sandbox. Use absolute input/output paths:

```sh
"/Applications/Xcode.app/Contents/Applications/Icon Composer.app/Contents/Executables/ictool" \
  "$PWD/apple/PickerRoyApple/AppIcon.icon" --export-image \
  --output-file "$PWD/work/PickerRoy-Default-iOS26.png" \
  --platform iOS --rendition Default --width 1024 --height 1024 --scale 1 \
  --design-generation 26
```

Other checked renditions: `Dark`, `TintedLight`, `TintedDark`, `ClearLight`, `ClearDark`. For actual-size inspection, export at width/height 64 rather than judging only the 1024px canvas. If the source foreground is regenerated, also update the copy in the `.icon` package and rerun native builds.

Official references: [Icon Composer](https://developer.apple.com/icon-composer/), [SwiftUI Liquid Glass](https://developer.apple.com/documentation/swiftui/applying-liquid-glass-to-custom-views).
