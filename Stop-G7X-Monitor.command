#!/bin/bash
# Pause the G7X monitor. It stays stopped across reboots until you run
# Start-G7X-Monitor.command. This does NOT uninstall it.
LABEL="com.g7xmonitor.agent"
UID_NUM="$(id -u)"

# disable = persistent (survives reboot); bootout = stop the running instance.
launchctl disable "gui/$UID_NUM/$LABEL" 2>/dev/null || true
launchctl bootout "gui/$UID_NUM/$LABEL" 2>/dev/null || true

echo ""
echo "  ⏸  G7X monitor paused. It will stay stopped, even after a reboot."
echo "     Double-click Start-G7X-Monitor.command to resume."
echo ""
read -r -p "  Press return to close. " _ || true
