#!/bin/bash
# Creates "Account Tracker.app" in your Applications folder. It opens the tracker
# in its own app window (no tabs or address bar), then opens it.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
HTML="$DIR/index.html"
APP="$HOME/Applications/Account Tracker.app"

mkdir -p "$APP/Contents/MacOS"
cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Account Tracker</string>
  <key>CFBundleExecutable</key><string>launch</string>
  <key>CFBundleIdentifier</key><string>local.account-tracker</string>
  <key>CFBundlePackageType</key><string>APPL</string>
</dict></plist>
PLIST

cat > "$APP/Contents/MacOS/launch" <<LAUNCH
#!/bin/bash
HTML="$HTML"
URL="file://\${HTML// /%20}"
for B in "Google Chrome" "Microsoft Edge" "Brave Browser"; do
  if open -Ra "\$B" 2>/dev/null; then exec open -na "\$B" --args --app="\$URL"; fi
done
exec open "\$HTML"
LAUNCH
chmod +x "$APP/Contents/MacOS/launch"

# Add it to the Dock (once)
if ! defaults read com.apple.dock persistent-apps 2>/dev/null | grep -q "Account%20Tracker.app"; then
  defaults write com.apple.dock persistent-apps -array-add \
    "<dict><key>tile-data</key><dict><key>file-data</key><dict><key>_CFURLString</key><string>$APP</string><key>_CFURLStringType</key><integer>0</integer></dict></dict></dict>"
  killall Dock
fi

open "$APP"
echo
echo "Done. \"Account Tracker\" is in your Dock and in the Applications folder in your home folder."
echo "If you move this folder, run this installer again."
