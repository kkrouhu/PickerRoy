#!/bin/bash
set -euo pipefail

# Shipping Core Image implementation, synthetic images only; no user media.
pickerroy_repo="$(cd "$(dirname "$0")/.." && pwd)"
pickerroy_check_dir="$(mktemp -d "${TMPDIR:-/tmp}/pickerroy-native-enhancement.XXXXXX")"
mkdir -p "$pickerroy_repo/work/swift-module-cache"
xcrun swiftc -module-cache-path "$pickerroy_repo/work/swift-module-cache" \
    "$pickerroy_repo/apple/PickerRoyApple/Models.swift" \
    "$pickerroy_repo/apple/PickerRoyApple/AnalysisControl.swift" \
    "$pickerroy_repo/apple/PickerRoyApple/AnalysisEngine.swift" \
    "$pickerroy_repo/scripts/tests/NativeAdaptiveEnhancementCheck.swift" \
    -o "$pickerroy_check_dir/native-adaptive-enhancement-check"
"$pickerroy_check_dir/native-adaptive-enhancement-check" "$pickerroy_check_dir"
