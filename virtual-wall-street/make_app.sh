#!/bin/bash
# Creates "Virtual Wall Street.app" so the game opens like any other Mac app.
# Run it once from this folder:   bash make_app.sh
# Run it again if you move this folder or install a different Python.

set -e

GAME_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$(command -v python3 || true)"
# The main Applications folder (the one in Finder's sidebar) if we may write there,
# otherwise the Applications folder in your home folder.
if [ -w /Applications ]; then APPS="/Applications"; else APPS="$HOME/Applications"; fi
APP="$APPS/Virtual Wall Street.app"

if [ -z "$PYTHON" ]; then
  echo "Couldn't find python3. Install Python from python.org first."
  exit 1
fi
if ! "$PYTHON" -c "import alpaca, anthropic, dotenv" 2>/dev/null; then
  echo "The game's libraries aren't installed for $PYTHON yet. Run this first:"
  echo "  $PYTHON -m pip install -r requirements.txt"
  exit 1
fi

# macOS privacy protection blocks apps from reading Downloads, Desktop and Documents
# without permission, so the app couldn't start a game kept there. Terminal usually has
# that permission already, which is why running city.py by hand still works.
case "$GAME_DIR" in
  "$HOME/Downloads"*|"$HOME/Desktop"*|"$HOME/Documents"*)
    echo "This folder is inside Downloads, Desktop or Documents, which macOS protects:"
    echo "the app wouldn't be allowed to start the game from here. Move it to your"
    echo "home folder first, then run this script again from there:"
    echo "  mv \"$GAME_DIR\" ~/virtual-wall-street"
    echo "  cd ~/virtual-wall-street && bash make_app.sh"
    exit 1
    ;;
esac

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

# The app is a plain shell script, not an AppleScript applet (those can be silently
# blocked) and not compiled code, so there is nothing to sign. If the game is already
# running it just opens the city; otherwise it starts the game in the background
# (no Terminal window), waits for it to come up, then opens the city.
{
  echo '#!/bin/bash'
  echo "GAME_DIR=\"$GAME_DIR\""
  echo "PYTHON=\"$PYTHON\""
  cat <<'LAUNCHER'
URL="http://localhost:8765"

running() { /usr/bin/curl -s -o /dev/null --max-time 1 "$URL/api/state"; }

if ! running; then
  cd "$GAME_DIR" || exit 1
  nohup "$PYTHON" city.py --no-browser > city.log 2>&1 &
  for i in $(seq 1 60); do
    sleep 0.25
    running && break
  done
  if ! running; then
    details=$(tail -n 12 "$GAME_DIR/city.log" 2>/dev/null | tr '"\\' "''")
    /usr/bin/osascript -e "display dialog \"Virtual Wall Street didn't start.

$details\" buttons {\"OK\"} with icon caution" >/dev/null
    exit 1
  fi
fi
/usr/bin/open "$URL"
LAUNCHER
} > "$APP/Contents/MacOS/launcher"
chmod +x "$APP/Contents/MacOS/launcher"

cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>Virtual Wall Street</string>
  <key>CFBundleDisplayName</key><string>Virtual Wall Street</string>
  <key>CFBundleIdentifier</key><string>local.virtual-wall-street</string>
  <key>CFBundleVersion</key><string>1.0</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleExecutable</key><string>launcher</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>LSUIElement</key><true/>
</dict>
</plist>
PLIST

# App icon from web/icon.png (optional: the app works without it).
if [ -f "$GAME_DIR/web/icon.png" ] && command -v iconutil >/dev/null; then
  ICONSET="$(mktemp -d)/AppIcon.iconset"
  mkdir -p "$ICONSET"
  for size in 16 32 128 256 512; do
    sips -z $size $size "$GAME_DIR/web/icon.png" --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
    double=$((size * 2))
    sips -z $double $double "$GAME_DIR/web/icon.png" --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
  done
  iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/AppIcon.icns" || true
  rm -rf "$(dirname "$ICONSET")"
fi

xattr -cr "$APP" 2>/dev/null || true
touch "$APP"

echo ""
echo "Done! \"Virtual Wall Street\" is in $APPS:"
echo "  $APP"
echo ""
echo "Open it from Finder > Applications, Launchpad or Spotlight (Cmd+Space)."
echo "Tip: drag it to your Dock to keep it one click away."
open -R "$APP"
