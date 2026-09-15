import CoreGraphics
import Darwin
import Foundation
import ImageIO
import UniformTypeIdentifiers

private struct CheckFailure: Error, CustomStringConvertible { let description: String }
private func expect(_ condition: @autoclosure () -> Bool, _ message: String) throws {
    if !condition() { throw CheckFailure(description: message) }
}

@main
struct NativeAdaptiveEnhancementCheck {
    private static let space = CGColorSpace(name: CGColorSpace.sRGB)!

    static func main() {
        do { try run() }
        catch {
            FileHandle.standardError.write(Data("FAIL: \(error)\n".utf8))
            exit(1)
        }
    }

    private static func run() throws {
        let root = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
        let engine = AnalysisEngine()
        var random: UInt64 = 27
        let fixtures: [(String, CGImage)] = [
            ("flat-gray", image { _, _ in (0.42, 0.42, 0.42) }),
            ("black", image { _, _ in (0, 0, 0) }),
            ("white", image { _, _ in (1, 1, 1) }),
            ("low-contrast", image { x, _ in let v = 0.32 + 0.35 * Double(x) / 255; return (v, v, v) }),
            ("shadow-detail", image { x, y in let v = 0.08 + 0.29 * Double(x) / 255 + 0.01 * sin(Double(y) * 0.12); return (v, v, v) }),
            ("bright-sky-dark-foreground", image { x, y in
                let v = y < 108 ? 0.80 + 0.18 * Double(x) / 255 : 0.07 + 0.20 * Double(x) / 255
                return (v, v, v)
            }),
            ("bright-sky-colored-foreground", image { x, y in
                let v = y < 108 ? 0.80 + 0.18 * Double(x) / 255 : 0.10 + 0.20 * Double(x) / 255
                return y < 108 ? (v * 0.78, v * 0.86, v) : (v * 0.75, v, v * 0.65)
            }),
            ("highlight-ramp", image { x, _ in let v = 0.78 + 0.22 * Double(x) / 255; return (v, v, v) }),
            ("muted-color", image { x, _ in let v = 0.30 + 0.32 * Double(x) / 255; return (v * 0.88, v * 0.95, v) }),
            ("saturated-color", image { x, _ in let v = 0.40 + 0.5 * Double(x) / 255; return (v, v * 0.12, v * 0.08) }),
            ("skin-like", image { x, _ in let v = 0.40 + 0.38 * Double(x) / 255; return (v, v * 0.76, v * 0.62) }),
            ("soft-structure", image { x, y in let v = 0.45 + 0.16 * sin(Double(x) * 0.17) + 0.08 * sin(Double(y) * 0.14); return (v, v, v) }),
            ("severe-blur", image { x, y in let v = 0.4 + 0.15 * sin(Double(x) * 0.007) + 0.06 * sin(Double(y) * 0.009); return (v, v, v) }),
            ("noise", image { x, _ in
                random = random &* 6364136223846793005 &+ 1442695040888963407
                let v = 0.25 + 0.15 * Double(x) / 255 + (Double((random >> 32) & 255) / 255 - 0.5) * 0.20
                return (v, v, v)
            }),
            ("sharp-structure", image { x, y in let v = ((x / 2 + y / 2) % 2 == 0) ? 0.18 : 0.85; return (v, v, v) })
        ]
        var recipes: [String: AnalysisEngine.EnhancementRecipe] = [:]
        for (name, input) in fixtures {
            let originalBytes = pixels(input)
            let recipe = engine.enhancementRecipe(for: input)
            recipes[name] = recipe
            let output = engine.optimize(input)
            let result = pixels(output)
            try expect(output.width == input.width && output.height == input.height, "\(name): no upscaling/resampling")
            try expect(originalBytes == pixels(input), "\(name): source pixels must not be mutated")
            try expect(recipe.contrast >= 0 && recipe.contrast <= 0.22, "\(name): bounded contrast")
            try expect(recipe.shadows >= 0 && recipe.shadows <= 0.065, "\(name): bounded shadow lift")
            try expect(recipe.vibrance >= 0 && recipe.vibrance <= 0.18, "\(name): bounded color boost")
            try expect(recipe.sharpness >= 0 && recipe.sharpness <= 0.045, "\(name): micro-sharpening ceiling")
            let before = stats(originalBytes), after = stats(result)
            switch name {
            case "black", "white", "flat-gray":
                try expect(recipe.isIdentity && originalBytes == result, "\(name): constant image identity")
            case "low-contrast":
                try expect(after.span > before.span + 0.025, "Dull image must gain visible tonal separation")
            case "shadow-detail":
                try expect(after.mean > before.mean + 0.008, "Shadow detail should be gently lifted")
                try expect(after.span > before.span * 0.90, "Shadow lift must retain local tonal variation")
            case "bright-sky-dark-foreground":
                try expect(recipe.shadows > 0.025, "Bright sky must not disable dark-foreground enhancement")
                var shadowChanges: [Double] = [], highlightChanges: [Double] = []
                for p in stride(from: 0, to: result.count, by: 4) {
                    let inputValue = Double(originalBytes[p]) / 255
                    let change = Double(result[p]) / 255 - inputValue
                    if inputValue < 0.30 { shadowChanges.append(change) }
                    if inputValue > 0.75 { highlightChanges.append(change) }
                }
                try expect(shadowChanges.reduce(0, +) / Double(shadowChanges.count) > 0.018,
                           "Dark foreground must visibly lift despite a bright global median")
                try expect(highlightChanges.map(abs).reduce(0, +) / Double(highlightChanges.count) < 0.008,
                           "Shadow enhancement must leave the bright sky essentially unchanged")
            case "bright-sky-colored-foreground":
                var originalShadows: [UInt8] = [], enhancedShadows: [UInt8] = []
                for p in stride(from: 0, to: result.count, by: 4) where originalBytes[p + 1] < 80 {
                    originalShadows.append(contentsOf: originalBytes[p..<(p + 4)])
                    enhancedShadows.append(contentsOf: result[p..<(p + 4)])
                }
                let shadowBefore = stats(originalShadows), shadowAfter = stats(enhancedShadows)
                try expect(shadowAfter.mean > shadowBefore.mean + 0.015, "Colored foreground must visibly lift")
                try expect(shadowAfter.saturation >= shadowBefore.saturation - 0.012,
                           "Lifting shadows must not wash color out with an additive white offset")
                try expect(shadowAfter.saturation <= shadowBefore.saturation + 0.035,
                           "Color in the lifted foreground remains restrained")
            case "muted-color":
                try expect(after.saturation > before.saturation + 0.004, "Muted colors should gain restrained color")
            case "highlight-ramp":
                try expect(after.clipFraction <= before.clipFraction + 0.02, "Highlight adjustment must not materially expand clipping")
                try expect(Set(result.enumerated().filter { $0.offset % 4 == 0 }.map(\.element)).count >= 42, "Keep highlight gradation")
            case "saturated-color":
                try expect(after.saturation <= before.saturation + 0.015, "Protect already saturated color")
            case "skin-like":
                try expect(after.saturation <= before.saturation + 0.02, "Protect warm skin-like color")
            case "noise":
                try expect(recipe.sharpness == 0 && recipe.shadows == 0, "Noise must disable sharpening and shadow amplification")
            case "severe-blur", "sharp-structure":
                try expect(recipe.sharpness == 0, "\(name): do not sharpen")
            case "soft-structure":
                try expect(recipe.sharpness > 0, "Clean mildly soft structure should allow a small edge adjustment")
            default: break
            }
            if !["muted-color", "saturated-color", "skin-like", "bright-sky-colored-foreground"].contains(name) {
                for p in stride(from: 0, to: result.count, by: 4) {
                    try expect(abs(Int(result[p]) - Int(result[p + 1])) <= 1 && abs(Int(result[p + 1]) - Int(result[p + 2])) <= 1,
                               "\(name): gray images must remain neutral")
                }
            }
            try write(input, to: root.appendingPathComponent("\(name)-original.png"))
            try write(output, to: root.appendingPathComponent("\(name)-enhanced.png"))
            print(String(format: "PASS %@: contrast=%.4f shadows=%.4f color=%.4f sharpen=%.4f noise=%.4f gradient=%.4f span %.4f→%.4f mean %.4f→%.4f saturation %.4f→%.4f", name, recipe.contrast, recipe.shadows, recipe.vibrance, recipe.sharpness, recipe.noise, recipe.gradient, before.span, after.span, before.mean, after.mean, before.saturation, after.saturation))
        }
        let tiny = image(width: 1, height: 1) { _, _ in (0.24, 0.48, 0.60) }
        try expect(engine.optimize(tiny).width == 1 && engine.optimize(tiny).height == 1, "Tiny input is safe")
        let large = image(width: 1536, height: 864) { x, _ in let v = 0.3 + 0.35 * Double(x) / 1535; return (v, v, v) }
        let largeOutput = engine.optimize(large)
        try expect(largeOutput.width == 1536 && largeOutput.height == 864, "Large input dimensions retained")
        print("All native adaptive enhancement checks passed. Synthetic evidence: \(root.path)")
    }

    private static func image(width: Int = 256, height: Int = 160, color: (Int, Int) -> (Double, Double, Double)) -> CGImage {
        var bytes = [UInt8](repeating: 255, count: width * height * 4)
        for y in 0..<height {
            for x in 0..<width {
                let rgb = color(x, y), p = (y * width + x) * 4
                bytes[p] = UInt8((rgb.0 * 255).rounded().clamped(to: 0...255))
                bytes[p + 1] = UInt8((rgb.1 * 255).rounded().clamped(to: 0...255))
                bytes[p + 2] = UInt8((rgb.2 * 255).rounded().clamped(to: 0...255))
            }
        }
        let provider = CGDataProvider(data: Data(bytes) as CFData)!
        return CGImage(width: width, height: height, bitsPerComponent: 8, bitsPerPixel: 32, bytesPerRow: width * 4,
                       space: space, bitmapInfo: CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedLast.rawValue), provider: provider,
                       decode: nil, shouldInterpolate: false, intent: .defaultIntent)!
    }

    private static func pixels(_ image: CGImage) -> [UInt8] {
        var bytes = [UInt8](repeating: 0, count: image.width * image.height * 4)
        bytes.withUnsafeMutableBytes { raw in
            let context = CGContext(data: raw.baseAddress, width: image.width, height: image.height,
                bitsPerComponent: 8, bytesPerRow: image.width * 4, space: space,
                bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
            context.draw(image, in: CGRect(x: 0, y: 0, width: image.width, height: image.height))
        }
        return bytes
    }

    private static func stats(_ bytes: [UInt8]) -> (mean: Double, span: Double, saturation: Double, clipFraction: Double) {
        var luminances: [Double] = [], saturation = 0.0, clipped = 0
        for p in stride(from: 0, to: bytes.count, by: 4) {
            let r = Double(bytes[p]) / 255, g = Double(bytes[p + 1]) / 255, b = Double(bytes[p + 2]) / 255
            let high = max(r, max(g, b)), low = min(r, min(g, b))
            luminances.append(0.2126 * r + 0.7152 * g + 0.0722 * b)
            saturation += high > 0 ? (high - low) / high : 0
            if high >= 0.995 || low <= 0.005 { clipped += 1 }
        }
        let sorted = luminances.sorted(), n = Double(sorted.count)
        return (sorted.reduce(0, +) / n, sorted[Int((n - 1) * 0.95)] - sorted[Int((n - 1) * 0.05)], saturation / n, Double(clipped) / n)
    }

    private static func write(_ image: CGImage, to url: URL) throws {
        guard let destination = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else {
            throw CheckFailure(description: "Cannot create synthetic image")
        }
        CGImageDestinationAddImage(destination, image, nil)
        try expect(CGImageDestinationFinalize(destination), "Cannot write synthetic image")
    }
}
