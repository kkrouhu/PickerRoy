import SwiftUI
import CoreGraphics

/// Original vector lettering; shared by the navigation mark and generated app icon.
/// Coordinates follow a top-left origin. The O is a six-blade photographic iris.
enum RoyMarkGeometry {
    static let size = CGSize(width: 103, height: 34)

    static var ink: CGPath {
        let path = CGMutablePath()
        // R: the counter is a separate even-odd subpath, not a font-dependent glyph.
        path.move(to: CGPoint(x: 0, y: 0))
        path.addLine(to: CGPoint(x: 14, y: 0))
        path.addCurve(to: CGPoint(x: 27, y: 11), control1: CGPoint(x: 22.7, y: 0), control2: CGPoint(x: 27, y: 4.1))
        path.addCurve(to: CGPoint(x: 20.5, y: 21), control1: CGPoint(x: 27, y: 16), control2: CGPoint(x: 24.7, y: 19.3))
        path.addLine(to: CGPoint(x: 29, y: 34))
        path.addLine(to: CGPoint(x: 19, y: 34))
        path.addLine(to: CGPoint(x: 11.7, y: 22.3))
        path.addLine(to: CGPoint(x: 8.5, y: 22.3))
        path.addLine(to: CGPoint(x: 8.5, y: 34))
        path.addLine(to: CGPoint(x: 0, y: 34))
        path.closeSubpath()
        path.move(to: CGPoint(x: 8.5, y: 7.1))
        path.addLine(to: CGPoint(x: 13.5, y: 7.1))
        path.addCurve(to: CGPoint(x: 18.5, y: 11.2), control1: CGPoint(x: 16.9, y: 7.1), control2: CGPoint(x: 18.5, y: 8.4))
        path.addCurve(to: CGPoint(x: 13.5, y: 15.5), control1: CGPoint(x: 18.5, y: 14.1), control2: CGPoint(x: 16.9, y: 15.5))
        path.addLine(to: CGPoint(x: 8.5, y: 15.5))
        path.closeSubpath()

        path.move(to: CGPoint(x: 69, y: 0))
        path.addLine(to: CGPoint(x: 79, y: 0))
        path.addLine(to: CGPoint(x: 86, y: 12.3))
        path.addLine(to: CGPoint(x: 93, y: 0))
        path.addLine(to: CGPoint(x: 103, y: 0))
        path.addLine(to: CGPoint(x: 90.3, y: 21.4))
        path.addLine(to: CGPoint(x: 90.3, y: 34))
        path.addLine(to: CGPoint(x: 81.7, y: 34))
        path.addLine(to: CGPoint(x: 81.7, y: 21.4))
        path.closeSubpath()
        return path
    }

    static var opening: CGPath {
        let path = CGMutablePath()
        for index in 0..<6 {
            let point = irisPoint(index: index)
            if index == 0 { path.move(to: point) } else { path.addLine(to: point) }
        }
        path.closeSubpath()
        return path
    }

    /// The same iris silhouette, opening and six seams, with no solid blade fill.
    static var apertureOutline: CGPath {
        let path = CGMutablePath()
        // Inset by half the display stroke to preserve the original outer size.
        path.addEllipse(in: CGRect(x: 32.2, y: 0.2, width: 33.6, height: 33.6))
        path.addPath(opening)
        path.addPath(seams)
        return path
    }

    static func apertureLineWidth(small: Bool) -> CGFloat { small ? 1.65 : 1.2 }

    static var seams: CGPath {
        let path = CGMutablePath()
        let innerRadius: CGFloat = 6.2
        let outerRadius: CGFloat = 16.8
        let reach = -innerRadius / 2 + sqrt(outerRadius * outerRadius - 3 * innerRadius * innerRadius / 4)
        for index in 0..<6 {
            let inner = irisPoint(index: index)
            let direction = CGFloat(index) * .pi / 3 - .pi / 6 + .pi / 3
            path.move(to: inner)
            path.addLine(to: CGPoint(x: inner.x + cos(direction) * reach, y: inner.y + sin(direction) * reach))
        }
        return path
    }

    private static func irisPoint(index: Int) -> CGPoint {
        let angle = CGFloat(index) * .pi / 3 - .pi / 6
        return CGPoint(x: 49 + cos(angle) * 6.2, y: 17 + sin(angle) * 6.2)
    }

    static func wordmarkRect(in bounds: CGRect) -> CGRect {
        let width = bounds.width * 0.74
        let height = width * size.height / size.width
        return CGRect(x: bounds.midX - width / 2, y: bounds.midY - height / 2, width: width, height: height)
    }

    /// Call in a top-left coordinate system; transparent backgrounds are supported.
    static func draw(in context: CGContext, bounds: CGRect, small: Bool = false) {
        let rect = wordmarkRect(in: bounds)
        context.saveGState()
        context.translateBy(x: rect.minX, y: rect.minY)
        context.scaleBy(x: rect.width / size.width, y: rect.height / size.height)
        context.setFillColor(CGColor(gray: 0.025, alpha: 1))
        context.addPath(ink)
        context.drawPath(using: .eoFill)
        context.setStrokeColor(CGColor(gray: 0.025, alpha: 1))
        context.setLineWidth(apertureLineWidth(small: small))
        context.setLineCap(.round)
        context.setLineJoin(.round)
        context.addPath(apertureOutline)
        context.strokePath()
        context.restoreGState()
    }
}

struct RoyBrandBadge: View {
    var forceOpaque = false
    @Environment(\.accessibilityReduceTransparency) private var reduceTransparency
    @Environment(\.colorScheme) private var colorScheme

    var body: some View {
        GeometryReader { geometry in
            Canvas { context, size in
                let rect = RoyMarkGeometry.wordmarkRect(in: CGRect(origin: .zero, size: size))
                context.translateBy(x: rect.minX, y: rect.minY)
                context.scaleBy(x: rect.width / RoyMarkGeometry.size.width, y: rect.height / RoyMarkGeometry.size.height)
                context.fill(Path(RoyMarkGeometry.ink), with: .foreground, style: FillStyle(eoFill: true))
                context.stroke(Path(RoyMarkGeometry.apertureOutline), with: .foreground,
                               style: StrokeStyle(lineWidth: RoyMarkGeometry.apertureLineWidth(small: size.width <= 64),
                                                  lineCap: .round, lineJoin: .round))
            }
            .foregroundStyle(.primary)
            .modifier(RoyGlassBackground(cornerRadius: geometry.size.width * 0.235, reduceTransparency: reduceTransparency || forceOpaque,
                                         dark: colorScheme == .dark))
        }
        .aspectRatio(1, contentMode: .fit)
        .accessibilityHidden(true)
    }
}

private struct RoyGlassBackground: ViewModifier {
    let cornerRadius: CGFloat
    let reduceTransparency: Bool
    let dark: Bool

    @ViewBuilder func body(content: Content) -> some View {
        let shape = RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
        if #available(iOS 26.0, macOS 26.0, *), !reduceTransparency {
            content.glassEffect(.regular.tint(.white.opacity(dark ? 0.08 : 0.24)), in: shape)
        } else {
            content.background(dark ? Color(white: 0.16) : .white, in: shape)
                .overlay(shape.strokeBorder(.primary.opacity(0.08), lineWidth: 0.5))
        }
    }
}
