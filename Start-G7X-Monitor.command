#!/bin/bash
# Resume the G7X monitor after a pause (see Stop-G7X-Monitor.command).
LABEL="com.g7xmonitor.agent"
UID_NUM="$(id -u)"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

if [ ! -f "$PLIST" ]; then
  echo ""
  echo "  ✗ The monitor isn't installed (no LaunchAgent found)."
  echo "    Install it first: run install.sh, the installer, or 'brew install g7x-monitor'."
  echo ""
  read -r -p "  Press return to close. " _ || true
  exit 1
fi

launchctl enable "gui/$UID_NUM/$LABEL" 2>/dev/null || true
launchctl bootout "gui/$UID_NUM/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$UID_NUM" "$PLIST"

echo ""
echo "  ▶  G7X monitor started — watching again (checks every ~2-3 min)."
echo "     Pause it anytime with Stop-G7X-Monitor.command."
echo ""
read -r -p "  Press return to close. " _ || true
