import SwiftUI

@main
struct PickerRoyApp: App {
    @StateObject private var model = PickerRoyModel()

    var body: some Scene {
        WindowGroup {
            #if os(macOS)
            ContentView()
                .environmentObject(model)
                .frame(minWidth: 920, minHeight: 620)
            #else
            ContentView()
                .environmentObject(model)
            #endif
        }
    }
}
