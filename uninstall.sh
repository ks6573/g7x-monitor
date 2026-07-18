#!/bin/bash
# Stop + remove the G7X MSRP monitor LaunchAgent.
set -euo pipefail

LABEL="com.g7xmonitor.agent"
PLIST_DST="$HOME/Library/LaunchAgents/$LABEL.plist"
UID_NUM="$(id -u)"

launchctl bootout "gui/$UID_NUM/$LABEL" 2>/dev/null || true
rm -f "$PLIST_DST"
echo "Stopped and removed $LABEL."
echo "(Chrome profile, logs, and state were kept. Delete the project folder to remove everything.)"
