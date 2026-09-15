#!/bin/bash
set -euo pipefail

# Value-state tests only: no window, UserDefaults write, account or real consent.
pickerroy_repo="$(cd "$(dirname "$0")/.." && pwd)"
pickerroy_check_dir="$(mktemp -d "${TMPDIR:-/tmp}/pickerroy-native-notice.XXXXXX")"
mkdir -p "$pickerroy_repo/work/swift-module-cache"
xcrun swiftc -module-cache-path "$pickerroy_repo/work/swift-module-cache" \
    "$pickerroy_repo/apple/PickerRoyApple/Models.swift" \
    "$pickerroy_repo/apple/PickerRoyApple/AnalysisControl.swift" \
    "$pickerroy_repo/apple/PickerRoyApple/AnalysisEngine.swift" \
    "$pickerroy_repo/apple/PickerRoyApple/PreferenceStore.swift" \
    "$pickerroy_repo/apple/PickerRoyApple/FeatureAccessPolicy.swift" \
    "$pickerroy_repo/apple/PickerRoyApple/PickerRoyModel.swift" \
    "$pickerroy_repo/apple/PickerRoyApple/ContentView.swift" \
    "$pickerroy_repo/scripts/tests/NativeMaterialNoticeCheck.swift" \
    -o "$pickerroy_check_dir/native-material-notice-check"
"$pickerroy_check_dir/native-material-notice-check"
