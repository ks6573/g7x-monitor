"""Per-retailer alert state: edge-trigger on restock, plus periodic re-alert.

State shape: {retailer: {"in_stock": bool, "last_alert": epoch_seconds}}
"""
import json
from pathlib import Path


def _entry(state, retailer):
    return state.get(retailer, {"in_stock": False, "last_alert": 0})


def should_alert(state, retailer, qualifying, now, realert_seconds):
    """Alert when a retailer newly qualifies (out->in), or has stayed
    qualifying for at least `realert_seconds` since the last alert."""
    if not qualifying:
        return False
    entry = _entry(state, retailer)
    if not entry["in_stock"]:
        return True
    return (now - entry["last_alert"]) >= realert_seconds


def record(state, retailer, qualifying, now, alerted):
    """Persist the retailer's current status; bump last_alert only if we alerted."""
    entry = state.setdefault(retailer, {"in_stock": False, "last_alert": 0})
    entry["in_stock"] = qualifying
    if alerted:
        entry["last_alert"] = now


def load_state(path):
    path = Path(path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(path, state):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))
