"""macOS alerting: a loud, hard-to-miss notification for an MSRP restock.

`build_alert` is pure (unit-tested). `notify` performs the macOS side effects
(banner + repeated sound + spoken announcement + optional page open) and is
smoke-tested only.
"""
import subprocess

SOUND_FILE = "/System/Library/Sounds/Glass.aiff"
SOUND_REPEATS = 3


def build_alert(result):
    """Return (title, message, speak_text) for a qualifying Result."""
    if result.price is not None:
        price_str = f"${result.price:.2f}"
        dollars = int(result.price)
    else:
        price_str = "price unknown"
        dollars = 0
    title = f"🚨 G7X III IN STOCK — {result.retailer}"
    message = f"{price_str} — {result.retailer}\n{result.url}"
    speak_text = (f"Canon G 7 X in stock at {result.retailer} "
                  f"for {dollars} dollars")
    return title, message, speak_text


def _run(cmd):
    """Best-effort external command; never raise into the monitor loop."""
    try:
        subprocess.run(cmd, check=False, timeout=30,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def notify(title, message, *, sound=True, speak_text=None, open_url=None):
    """Fire the macOS alert. Passing text via `argv` avoids AppleScript quoting."""
    _run(["osascript",
          "-e", "on run argv",
          "-e", "display notification (item 1 of argv) with title (item 2 of argv)",
          "-e", "end run",
          message, title])
    if sound:
        for _ in range(SOUND_REPEATS):
            _run(["afplay", SOUND_FILE])
    if speak_text:
        _run(["say", speak_text])
    if open_url:
        _run(["open", open_url])
