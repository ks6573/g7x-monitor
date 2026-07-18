#!/bin/bash
# Install + start the G7X MSRP monitor as a macOS LaunchAgent.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LABEL="com.g7xmonitor.agent"
LA_DIR="$HOME/Library/LaunchAgents"
PLIST_DST="$LA_DIR/$LABEL.plist"
UID_NUM="$(id -u)"

echo "==> Project: $PROJECT_DIR"

# 1) venv + dependencies
if [ ! -x "$PROJECT_DIR/.venv/bin/python" ]; then
  echo "==> Creating venv"
  python3 -m venv "$PROJECT_DIR/.venv"
fi
echo "==> Installing dependencies"
"$PROJECT_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$PROJECT_DIR/.venv/bin/pip" install --quiet -r "$PROJECT_DIR/requirements.txt"

# 2) We drive real Google Chrome (not bundled Chromium) to pass anti-bot.
if [ ! -d "/Applications/Google Chrome.app" ]; then
  echo "!! Google Chrome not found in /Applications. Install Chrome, then re-run." >&2
  exit 1
fi

# 3) Install the LaunchAgent with the absolute project path filled in.
mkdir -p "$LA_DIR" "$PROJECT_DIR/logs"
sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" "$PROJECT_DIR/$LABEL.plist" > "$PLIST_DST"
echo "==> Wrote $PLIST_DST"

# 4) (Re)load and start. Enable first, in case it was paused (disabled) before.
launchctl enable "gui/$UID_NUM/$LABEL" 2>/dev/null || true
launchctl bootout "gui/$UID_NUM/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$UID_NUM" "$PLIST_DST"

echo "==> Installed and started."
echo "    Live log:    tail -f \"$PROJECT_DIR/logs/monitor.log\""
echo "    Status:      launchctl list | grep g7xmonitor"
echo "    Stop/remove: \"$PROJECT_DIR/uninstall.sh\""
