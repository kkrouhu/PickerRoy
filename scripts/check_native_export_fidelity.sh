#!/bin/bash
set -euo pipefail

# Builds a small integration executable from the shipping engine/model sources.
# All fixtures are newly generated; existing media and exports are never touched.
pickerroy_repo="$(cd "$(dirname "$0")/.." && pwd)"
pickerroy_check_dir="$(mktemp -d "${TMPDIR:-/tmp}/pickerroy-native-export.XXXXXX")"
mkdir -p "$pickerroy_repo/work/swift-module-cache"
xcrun swiftc -module-cache-path "$pickerroy_repo/work/swift-module-cache" \
    "$pickerroy_repo/apple/PickerRoyApple/Models.swift" \
    "$pickerroy_repo/apple/PickerRoyApple/AnalysisControl.swift" \
    "$pickerroy_repo/apple/PickerRoyApple/AnalysisEngine.swift" \
    "$pickerroy_repo/scripts/tests/NativeExportFidelityCheck.swift" \
    -o "$pickerroy_check_dir/native-export-fidelity-check"
"$pickerroy_check_dir/native-export-fidelity-check" "$pickerroy_check_dir"
