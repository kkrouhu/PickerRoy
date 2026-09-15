# PickerRoy V1.0 Release Audit

Audit date: 2026-09-15

## Current result

- Core native processing is local: AVFoundation reads selected videos, Vision detects faces, Core Image evaluates and renders frames, and ImageIO writes exports.
- No video, photo, thumbnail, filename, file path, preference profile, or analysis result is sent off-device.
- No runtime network-request code was found in the native app or desktop core.
- No Firebase, Supabase, AWS, Google Cloud, Cloudflare, self-hosted backend, remote AI API, analytics SDK, crash-reporting SDK, advertising SDK, or tracking SDK was found.
- The native Apple target contains no third-party SDK. The desktop app uses local open-source runtime libraries listed in `pyproject.toml`; none is configured as analytics or cloud processing.
- URLs in privacy property-list DOCTYPE declarations are file-format identifiers, not runtime requests. GitHub Actions upload/download steps run only in the release build pipeline, not in the installed app.
- V1.0 contains no StoreKit code, IAP, subscription, paywall, price, upgrade button, purchase button, restore purchase, or feature lock.

## Permissions

### iPhone and iPad

- Input: system file picker grants access only to videos the user explicitly selects.
- Output: add-only Photos authorization is requested only when the user chooses to save selected frames to the system photo library.
- Not requested: full photo-library read access, camera, microphone, contacts, location, Bluetooth, local network, tracking, or notifications.

### Mac

- App Sandbox enabled.
- User-selected file read/write entitlement enabled.
- No network client/server entitlement is present.

## Privacy manifest

- Tracking: false.
- Tracking domains: none.
- Collected data types: none.
- Required Reason API: `UserDefaults`, reason `CA92.1`, used only for app-private visual preference settings.

## Offline release test

Static audit confirms that the import, analysis, ranking, personalization, rendering, and export code has no network dependency. Mac local processing has completed successfully without a service account or backend. The final flight-mode end-to-end check on a physical iPhone remains a release-gate test because simulator networking is not equivalent to a real device.

## Build and test evidence

- Automated desktop suite: 28 tests passed on 2026-09-15.
- Native macOS Release build: passed with Xcode 27.0, version 1.0.0, build 1.
- Native generic iOS Release build: passed with Xcode 27.0, version 1.0.0, build 1.
- Privacy manifest and macOS/iOS entitlement property lists: valid.
- Native binary dependency inspection: Apple system frameworks only. No embedded third-party framework was found.
- Release configuration excludes the optional demo-video injection because it is wrapped in `#if DEBUG`.
- The local command-line verification build disabled Swift's compiler-plugin sandbox only because the Codex workspace itself already runs inside a restricted sandbox. The normal Xcode GUI build succeeded without that diagnostic workaround.

## V1.0 identity and signing status

- Current Bundle Identifier: `com.roy.pickerroy`.
- Marketing Version: `1.0.0`.
- Build Number: `1`.
- Local unsigned Release builds are successful.
- Distribution signing, the final Team selection, App Store archive validation, and upload cannot be completed until an active Apple Developer Program team is available in Xcode.

## Review gates still requiring owner/device access

- Confirm the final, available Bundle Identifier and development team.
- Complete Apple Developer Program enrollment if the account is not yet active.
- Build, sign, and install on a physical iPhone.
- Test H.264, HEVC, 4K, HDR/SDR, long video, thermal behavior, memory use, cancellation, optimized export, add-only Photos permission, and airplane-mode workflow.
- Create the App Store Connect record and submit the final privacy answers, screenshots, support URL, and privacy-policy URL.
- Confirm any Mainland China distribution filing requirement shown by App Store Connect.
