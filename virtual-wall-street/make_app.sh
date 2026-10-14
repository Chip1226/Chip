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

mkdir -p "$APPS"
rm -rf "$APP"

# The app: if the game is already running, just open the city. Otherwise start it in
# the background (no Terminal window), wait for it to come up, then open the city.
SCRIPT="$(mktemp -t vws)"
cat > "$SCRIPT" <<EOF
set gameDir to "$GAME_DIR"
set py to "$PYTHON"
set gameURL to "http://localhost:8765"

on isRunning(gameURL)
	try
		do shell script "curl -s -o /dev/null --max-time 1 " & gameURL & "/api/state"
		return true
	on error
		return false
	end try
end isRunning

if not isRunning(gameURL) then
	do shell script "cd " & quoted form of gameDir & " && nohup " & quoted form of py & " city.py --no-browser > city.log 2>&1 &"
	set started to false
	repeat 60 times
		delay 0.25
		if isRunning(gameURL) then
			set started to true
			exit repeat
		end if
	end repeat
	if not started then
		set logTail to do shell script "tail -n 15 " & quoted form of (gameDir & "/city.log") & " 2>/dev/null || true"
		display dialog "Virtual Wall Street didn't start." & return & return & logTail buttons {"OK"} default button 1 with icon caution
		return
	end if
end if
open location gameURL
EOF
osacompile -o "$APP" "$SCRIPT"
rm -f "$SCRIPT"

# App icon from web/icon.png (optional: the app works without it).
if [ -f "$GAME_DIR/web/icon.png" ] && command -v iconutil >/dev/null; then
  ICONSET="$(mktemp -d)/AppIcon.iconset"
  mkdir -p "$ICONSET"
  for size in 16 32 128 256 512; do
    sips -z $size $size "$GAME_DIR/web/icon.png" --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
    double=$((size * 2))
    sips -z $double $double "$GAME_DIR/web/icon.png" --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
  done
  if iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/applet.icns"; then
    touch "$APP"
  fi
  rm -rf "$(dirname "$ICONSET")"
fi

# Changing the app after it's built (the icon above) breaks its signature, and Macs
# with Apple chips silently refuse to open apps with a broken signature. Re-sign it
# locally ("ad-hoc": no Apple developer account needed) and clear download flags.
xattr -cr "$APP" 2>/dev/null || true
codesign --force --deep --sign - "$APP"

echo ""
echo "Done! \"Virtual Wall Street\" is in $APPS:"
echo "  $APP"
echo ""
echo "Open it from Finder > Applications, Launchpad or Spotlight (Cmd+Space)."
echo "Tip: drag it to your Dock to keep it one click away."
open -R "$APP"
