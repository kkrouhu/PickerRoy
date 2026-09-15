import SwiftUI
import ImageIO
import UniformTypeIdentifiers

/// Static material-direction artwork. ImageRenderer cannot capture native glass;
/// this deliberately uses illustrative gradients, not a claimed system export.
private struct PreviewBoard: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 24) {
            Text("PickerRoy · 轻透背景设计方向")
                .font(.system(size: 23, weight: .semibold))
            HStack(spacing: 18) {
                sample(title: "浅色", dark: false, reduced: false)
                sample(title: "深色", dark: true, reduced: false)
                sample(title: "降低透明度", dark: false, reduced: true)
            }
            Text("材质方向示意，非系统最终渲染 · 原生分层图标待 Icon Composer 完成")
                .font(.system(size: 13)).foregroundStyle(.secondary)
        }
        .padding(32)
        .frame(width: 1000, height: 490)
        .background(Color(white: 0.96))
        .environment(\.colorScheme, .light)
    }

    private func sample(title: String, dark: Bool, reduced: Bool) -> some View {
        VStack(spacing: 20) {
            ZStack {
                LinearGradient(colors: dark ? [Color(white: 0.15), Color(red: 0.12, green: 0.17, blue: 0.20)] :
                                [Color(red: 0.93, green: 0.95, blue: 0.96), Color(red: 0.78, green: 0.84, blue: 0.85)],
                               startPoint: .topLeading, endPoint: .bottomTrailing)
                Ellipse().fill(.white.opacity(dark ? 0.1 : 0.55)).frame(width: 260, height: 45)
                    .rotationEffect(.degrees(-30)).blur(radius: 20).offset(x: -30, y: -40)
                let shape = RoundedRectangle(cornerRadius: 37.6, style: .continuous)
                ZStack {
                    if reduced {
                        shape.fill(.white)
                    } else {
                        shape.fill(LinearGradient(colors: dark ? [.white.opacity(0.20), .white.opacity(0.055)] :
                                                   [.white.opacity(0.90), .white.opacity(0.48)],
                                                  startPoint: .topLeading, endPoint: .bottomTrailing))
                            .overlay(shape.strokeBorder(LinearGradient(colors: [.white.opacity(dark ? 0.50 : 0.95), .white.opacity(0.10), .white.opacity(0.55)],
                                                                       startPoint: .topLeading, endPoint: .bottomTrailing), lineWidth: 1))
                            .shadow(color: .black.opacity(dark ? 0.12 : 0.08), radius: 9, y: 5)
                    }
                    Canvas { context, size in
                        let rect = RoyMarkGeometry.wordmarkRect(in: CGRect(origin: .zero, size: size))
                        context.translateBy(x: rect.minX, y: rect.minY)
                        context.scaleBy(x: rect.width / 103, y: rect.height / 34)
                        let color = Color(white: dark ? 0.98 : 0.025)
                        context.fill(Path(RoyMarkGeometry.ink), with: .color(color), style: FillStyle(eoFill: true))
                        context.stroke(Path(RoyMarkGeometry.apertureOutline), with: .color(color),
                                       style: StrokeStyle(lineWidth: 1.2, lineCap: .round, lineJoin: .round))
                    }
                }.frame(width: 160, height: 160)
            }
            .frame(height: 270).clipShape(RoundedRectangle(cornerRadius: 20))
            Text(title).font(.system(size: 16, weight: .medium))
        }
        .frame(maxWidth: .infinity)
    }
}

@main @MainActor
struct RenderGlassPreview {
    static func main() throws {
        let url = URL(fileURLWithPath: CommandLine.arguments[1])
        let renderer = ImageRenderer(content: PreviewBoard())
        renderer.scale = 2
        guard let image = renderer.cgImage,
              let output = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else {
            throw CocoaError(.fileWriteUnknown)
        }
        CGImageDestinationAddImage(output, image, nil)
        guard CGImageDestinationFinalize(output) else { throw CocoaError(.fileWriteUnknown) }
        print(url.path)
    }
}
