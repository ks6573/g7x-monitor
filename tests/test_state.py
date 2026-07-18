import json

from state import should_alert, record, load_state, save_state

REALERT = 900


def test_first_time_in_stock():
    s = {}
    assert should_alert(s, "bb", True, now=1000, realert_seconds=REALERT) is True


def test_still_in_stock_recent_no_realert():
    s = {"bb": {"in_stock": True, "last_alert": 1000}}
    assert should_alert(s, "bb", True, now=1100, realert_seconds=REALERT) is False


def test_still_in_stock_past_realert_window():
    s = {"bb": {"in_stock": True, "last_alert": 1000}}
    assert should_alert(s, "bb", True, now=2000, realert_seconds=REALERT) is True


def test_not_qualifying_never_alerts():
    s = {"bb": {"in_stock": True, "last_alert": 1000}}
    assert should_alert(s, "bb", False, now=5000, realert_seconds=REALERT) is False


def test_record_sets_in_stock_and_last_alert():
    s = {}
    record(s, "bb", True, now=1000, alerted=True)
    assert s["bb"]["in_stock"] is True
    assert s["bb"]["last_alert"] == 1000


def test_record_without_alert_keeps_last_alert():
    s = {"bb": {"in_stock": True, "last_alert": 1000}}
    record(s, "bb", True, now=1100, alerted=False)
    assert s["bb"]["last_alert"] == 1000
    assert s["bb"]["in_stock"] is True


def test_record_going_out_of_stock():
    s = {"bb": {"in_stock": True, "last_alert": 1000}}
    record(s, "bb", False, now=1200, alerted=False)
    assert s["bb"]["in_stock"] is False


def test_load_missing_file_returns_empty(tmp_path):
    assert load_state(tmp_path / "nope.json") == {}


def test_save_then_load_roundtrip(tmp_path):
    p = tmp_path / "state.json"
    s = {"bb": {"in_stock": True, "last_alert": 42}}
    save_state(p, s)
    assert load_state(p) == s
