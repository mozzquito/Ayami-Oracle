#!/bin/bash
# Builds QuackKeyboard.app as a standalone menu-bar app bundle from the
# SwiftPM executable. For local testing this ad-hoc signs the bundle;
# for distribution, sign with a Developer ID identity instead (see README).
set -euo pipefail

cd "$(dirname "$0")"

APP_NAME="Quack Keyboard"
BUNDLE_ID="com.mozzquito.quackkeyboard"
BUILD_DIR=".build/release"
APP_DIR=".build/${APP_NAME}.app"
SIGN_IDENTITY="${SIGN_IDENTITY:--}"  # "-" = ad-hoc; pass a Developer ID name to sign for real

echo "==> swift build -c release"
swift build -c release

echo "==> assembling ${APP_NAME}.app"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/Contents/MacOS" "$APP_DIR/Contents/Resources/Sounds"

cp "$BUILD_DIR/QuackKeyboard" "$APP_DIR/Contents/MacOS/QuackKeyboard"

if compgen -G "Resources/Sounds/*" > /dev/null; then
    cp Resources/Sounds/* "$APP_DIR/Contents/Resources/Sounds/"
else
    echo "!! WARNING: Resources/Sounds is empty — app will build but stay silent."
    echo "!! Add a few quack .wav files there before shipping (see README)."
fi

cat > "$APP_DIR/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleDisplayName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>${BUNDLE_ID}</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleExecutable</key>
    <string>QuackKeyboard</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

echo "==> codesign (identity: ${SIGN_IDENTITY})"
codesign --force --deep --sign "$SIGN_IDENTITY" "$APP_DIR"

echo "==> done: $APP_DIR"
echo "    Run:  open \"$APP_DIR\""
