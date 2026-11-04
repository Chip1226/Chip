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

open "$APP"
echo
echo "Done. \"Account Tracker\" is in your Applications folder (in your home folder)."
echo "Tip: while it's open, right-click its Dock icon > Options > Keep in Dock."
echo "If you move this folder, run this installer again."
