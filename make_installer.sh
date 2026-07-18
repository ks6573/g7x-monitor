#!/bin/bash
# Build a self-contained, double-clickable macOS installer that CARRIES the
# monitor's code inside it (base64 payload) — the end user needs no git, no
# download, and no hosting. Output: dist/Install-G7X-Monitor.command
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
DIST="$SRC/dist"
OUT="$DIST/Install-G7X-Monitor.command"
mkdir -p "$DIST"

# 1) Pack the runtime files only (no tests, docs, venv, or dev cruft).
#    COPYFILE_DISABLE stops macOS tar from embedding ._ AppleDouble files.
TARBALL="$(mktemp -t g7xpkg).tgz"
COPYFILE_DISABLE=1 tar czf "$TARBALL" -C "$SRC" \
  config.py monitor.py decision.py state.py alert.py \
  checkers/__init__.py checkers/base.py checkers/util.py \
  checkers/canon.py checkers/bestbuy.py checkers/bhphoto.py \
  checkers/target.py checkers/adorama.py checkers/amazon.py \
  requirements.txt README.md com.g7xmonitor.agent.plist \
  Stop-G7X-Monitor.command Start-G7X-Monitor.command

# 2) Emit the installer: header + embedded base64 payload + footer.
cat > "$OUT" <<'HEADER'
#!/bin/bash
# ============================================================================
#  Canon G7X Mark III — MSRP restock monitor  ·  self-contained installer
#  Double-click to install. No git, no download needed. macOS only.
# ============================================================================
set -euo pipefail

LABEL="com.g7xmonitor.agent"
INSTALL_DIR="${G7X_INSTALL_DIR:-$HOME/Library/Application Support/g7x-monitor}"
LA_DIR="$HOME/Library/LaunchAgents"
UID_NUM="$(id -u)"

echo ""
echo "  Canon G7X Mark III — MSRP restock monitor"
echo "  Installing to: $INSTALL_DIR"
echo ""

if ! command -v python3 >/dev/null 2>&1; then
  echo "  x  python3 not found. Install Apple Command Line Tools first:"
  echo "        xcode-select --install"
  echo "     then run this installer again."
  read -r -p "  Press return to close. " _ || true
  exit 1
fi
if [ ! -d "/Applications/Google Chrome.app" ]; then
  echo "  x  Google Chrome not found in /Applications."
  echo "     Install Chrome from https://www.google.com/chrome/ then re-run."
  read -r -p "  Press return to close. " _ || true
  exit 1
fi

mkdir -p "$INSTALL_DIR" "$INSTALL_DIR/logs" "$LA_DIR"
echo "  - Unpacking files..."
base64 -D <<'PAYLOAD' | tar xzf - -C "$INSTALL_DIR"
HEADER

base64 < "$TARBALL" >> "$OUT"

cat >> "$OUT" <<'FOOTER'
PAYLOAD

echo "  - Creating Python environment (this can take a minute)..."
python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"

# Write a matching uninstaller into the install dir.
cat > "$INSTALL_DIR/Uninstall-G7X-Monitor.command" <<UNINSTALL
#!/bin/bash
launchctl bootout "gui/\$(id -u)/$LABEL" 2>/dev/null || true
rm -f "$LA_DIR/$LABEL.plist"
echo "G7X monitor stopped and removed. Delete this folder to remove everything:"
echo "  $INSTALL_DIR"
read -r -p "Press return to close. " _ || true
UNINSTALL
chmod +x "$INSTALL_DIR/Uninstall-G7X-Monitor.command"

if [ "${G7X_DRY_RUN:-0}" = "1" ]; then
  echo "  - DRY RUN: skipping LaunchAgent load."
  echo "  ok  Files + venv ready at $INSTALL_DIR"
  exit 0
fi

echo "  - Installing background service..."
chmod +x "$INSTALL_DIR"/*.command 2>/dev/null || true
sed "s|__PROJECT_DIR__|$INSTALL_DIR|g" \
    "$INSTALL_DIR/com.g7xmonitor.agent.plist" > "$LA_DIR/$LABEL.plist"
launchctl enable "gui/$UID_NUM/$LABEL" 2>/dev/null || true
launchctl bootout "gui/$UID_NUM/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$UID_NUM" "$LA_DIR/$LABEL.plist"

echo ""
echo "  ok  Installed and running. It checks every ~2-3 minutes and alerts you"
echo "      (loud banner + sound + speech) the moment the G7X III is in stock"
echo "      at MSRP."
echo ""
echo "      Watch it:   tail -f \"$INSTALL_DIR/logs/monitor.log\""
echo "      Pause it:   double-click Stop-G7X-Monitor.command  (in $INSTALL_DIR)"
echo "      Resume it:  double-click Start-G7X-Monitor.command"
echo "      Uninstall:  double-click Uninstall-G7X-Monitor.command"
echo ""
read -r -p "  Press return to close. " _ || true
FOOTER

chmod +x "$OUT"
rm -f "$TARBALL"
echo "Built: $OUT"
du -h "$OUT" | awk '{print "  size:", $1}'
