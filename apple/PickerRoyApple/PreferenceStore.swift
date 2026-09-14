import Foundation

final class PreferenceStore {
    private let fileURL: URL

    init() {
        let manager = FileManager.default
        let root = manager.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
            .appendingPathComponent("PickerRoy", isDirectory: true)
        try? manager.createDirectory(at: root, withIntermediateDirectories: true)
        fileURL = root.appendingPathComponent("preference-profile.json")
    }

    func load() -> PreferenceProfile {
        guard let data = try? Data(contentsOf: fileURL),
              let profile = try? JSONDecoder().decode(PreferenceProfile.self, from: data)
        else { return PreferenceProfile() }
        return profile
    }

    func save(_ profile: PreferenceProfile) {
        guard let data = try? JSONEncoder().encode(profile) else { return }
        try? data.write(to: fileURL, options: .atomic)
    }

    func reset() {
        try? FileManager.default.removeItem(at: fileURL)
    }
}
