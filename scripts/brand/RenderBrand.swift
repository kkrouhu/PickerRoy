import AppKit
import CoreText
import ImageIO
import UniformTypeIdentifiers

/// Renders the app's own vector geometry, without editing or embedding the reference screenshot.
@main
struct RenderBrand {
    static func main() throws {
        let root = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
        try png(width: 1024, height: 1024, to: root.appendingPathComponent("PickerRoy/Assets.xcassets/AppIcon.appiconset/AppIcon.png")) { context in
            context.setFillColor(CGColor(gray: 1, alpha: 1))
            context.fill(CGRect(x: 0, y: 0, width: 1024, height: 1024))
            context.translateBy(x: 0, y: 1024)
            context.scaleBy(x: 1, y: -1)
            RoyMarkGeometry.draw(in: context, bounds: CGRect(x: 0, y: 0, width: 1024, height: 1024))
        }
        let output = root.deletingLastPathComponent().appendingPathComponent("PickerRoy-ROY标志.png")
        try png(width: 720, height: 520, to: output) { context in
            context.setFillColor(CGColor(red: 0.185, green: 0.185, blue: 0.19, alpha: 1))
            context.fill(CGRect(x: 0, y: 0, width: 720, height: 520))
            let tile = CGRect(x: 232, y: 170, width: 256, height: 256)
            context.saveGState()
            context.setShadow(offset: CGSize(width: 0, height: -8), blur: 20, color: CGColor(gray: 0, alpha: 0.13))
            context.setFillColor(CGColor(gray: 1, alpha: 1))
            context.addPath(CGPath(roundedRect: tile, cornerWidth: 60, cornerHeight: 60, transform: nil))
            context.fillPath()
            context.restoreGState()
            context.saveGState()
            context.translateBy(x: tile.minX, y: tile.maxY)
            context.scaleBy(x: 1, y: -1)
            RoyMarkGeometry.draw(in: context, bounds: CGRect(x: 0, y: 0, width: 256, height: 256))
            context.restoreGState()
            let title = NSAttributedString(string: "PickerRoy", attributes: [
                .font: NSFont.systemFont(ofSize: 32, weight: .medium),
                .foregroundColor: NSColor.white
            ])
            let line = CTLineCreateWithAttributedString(title)
            let width = CTLineGetTypographicBounds(line, nil, nil, nil)
            context.textPosition = CGPoint(x: (720 - width) / 2, y: 112)
            CTLineDraw(line, context)
        }
        print("Rendered AppIcon.png and \(output.path)")
        if CommandLine.arguments.count > 2 {
            let desktop = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
            // Keep the mark separate from the material: Icon Composer/system glass
            // supplies the background and lighting rather than baking them in.
            for (filename, small) in [("assets/PickerRoy-foreground.png", false),
                                      ("apple/PickerRoyApple/Assets.xcassets/BrandForeground.imageset/BrandForeground.png", true)] {
                try png(width: 1024, height: 1024, to: desktop.appendingPathComponent(filename), transparent: true) { context in
                    context.translateBy(x: 0, y: 1024)
                    context.scaleBy(x: 1, y: -1)
                    RoyMarkGeometry.draw(in: context, bounds: CGRect(x: 0, y: 0, width: 1024, height: 1024), small: small)
                }
            }
            let badge = desktop.appendingPathComponent("assets/PickerRoy-logo.png")
            try png(width: 1024, height: 1024, to: badge, transparent: true) { context in
                context.setFillColor(CGColor(gray: 1, alpha: 1))
                context.addPath(CGPath(roundedRect: CGRect(x: 0, y: 0, width: 1024, height: 1024), cornerWidth: 240, cornerHeight: 240, transform: nil))
                context.fillPath()
                context.translateBy(x: 0, y: 1024)
                context.scaleBy(x: 1, y: -1)
                RoyMarkGeometry.draw(in: context, bounds: CGRect(x: 0, y: 0, width: 1024, height: 1024))
            }
            let iconset = desktop.appendingPathComponent("work/PickerRoy.iconset", isDirectory: true)
            try FileManager.default.createDirectory(at: iconset, withIntermediateDirectories: true)
            for base in [16, 32, 128, 256, 512] {
                for scale in [1, 2] {
                    let pixels = base * scale
                    let suffix = scale == 1 ? "" : "@2x"
                    let url = iconset.appendingPathComponent("icon_\(base)x\(base)\(suffix).png")
                    try png(width: pixels, height: pixels, to: url, transparent: true) { context in
                        let side = CGFloat(pixels)
                        let rect = CGRect(x: side * 0.08, y: side * 0.08, width: side * 0.84, height: side * 0.84)
                        context.saveGState()
                        context.setShadow(offset: CGSize(width: 0, height: -side * 0.01), blur: side * 0.025, color: CGColor(gray: 0, alpha: 0.15))
                        context.setFillColor(CGColor(gray: 1, alpha: 1))
                        context.addPath(CGPath(roundedRect: rect, cornerWidth: side * 0.2, cornerHeight: side * 0.2, transform: nil))
                        context.fillPath()
                        context.restoreGState()
                        context.translateBy(x: 0, y: side)
                        context.scaleBy(x: 1, y: -1)
                        RoyMarkGeometry.draw(in: context, bounds: rect, small: pixels <= 64)
                    }
                }
            }
            print("Rendered desktop badge and iconset")
        }
    }

    private static func png(width: Int, height: Int, to url: URL, transparent: Bool = false, draw: (CGContext) -> Void) throws {
        try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
        guard let context = CGContext(data: nil, width: width, height: height, bitsPerComponent: 8,
                                      bytesPerRow: width * 4, space: CGColorSpace(name: CGColorSpace.sRGB)!,
                                      bitmapInfo: (transparent ? CGImageAlphaInfo.premultipliedLast : CGImageAlphaInfo.noneSkipLast).rawValue) else {
            throw CocoaError(.fileWriteUnknown)
        }
        context.setAllowsAntialiasing(true)
        draw(context)
        guard let image = context.makeImage(),
              let writer = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else {
            throw CocoaError(.fileWriteUnknown)
        }
        CGImageDestinationAddImage(writer, image, nil)
        guard CGImageDestinationFinalize(writer) else { throw CocoaError(.fileWriteUnknown) }
    }
}
