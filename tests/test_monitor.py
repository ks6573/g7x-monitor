from monitor import run_cycle, compute_deadline, is_expired, parse_args
from checkers.base import Result

CEILING = 879.99
REALERT = 900


class FakeChecker:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def check(self, context, url):
        self.calls += 1
        return self.result


class Boom:
    def check(self, context, url):
        raise RuntimeError("boom")


def spec(name, module_obj, url="u"):
    return {"name": name, "module_obj": module_obj, "url": url}


def cycle(specs, state, now, alerts):
    run_cycle(None, specs, state, now=now,
              alert_fn=lambda *a: alerts.append(a),
              ceiling=CEILING, realert_seconds=REALERT)


def test_alerts_on_qualifying_hit():
    alerts = []
    state = {}
    r = Result(retailer="bestbuy", url="u", in_stock=True, price=879.99)
    cycle([spec("bestbuy", FakeChecker(r))], state, 1000, alerts)
    assert len(alerts) == 1
    assert state["bestbuy"]["in_stock"] is True


def test_no_realert_within_window():
    alerts = []
    state = {}
    r = Result(retailer="bestbuy", url="u", in_stock=True, price=879.99)
    s = [spec("bestbuy", FakeChecker(r))]
    cycle(s, state, 1000, alerts)
    cycle(s, state, 1100, alerts)          # +100s, within 900s window
    assert len(alerts) == 1


def test_realert_after_window():
    alerts = []
    state = {}
    r = Result(retailer="bestbuy", url="u", in_stock=True, price=879.99)
    s = [spec("bestbuy", FakeChecker(r))]
    cycle(s, state, 1000, alerts)
    cycle(s, state, 2000, alerts)          # +1000s, past window
    assert len(alerts) == 2


def test_no_alert_when_not_qualifying():
    alerts = []
    state = {}
    r = Result(retailer="canon", url="u", in_stock=False, price=879.99)
    cycle([spec("canon", FakeChecker(r))], state, 1000, alerts)
    assert len(alerts) == 0


def test_price_above_ceiling_no_alert():
    alerts = []
    state = {}
    r = Result(retailer="adorama", url="u", in_stock=True, price=1299.0)
    cycle([spec("adorama", FakeChecker(r))], state, 1000, alerts)
    assert len(alerts) == 0


def test_checker_exception_is_isolated():
    alerts = []
    state = {}
    good = spec("bestbuy", FakeChecker(
        Result(retailer="bestbuy", url="u", in_stock=True, price=879.99)))
    bad = spec("canon", Boom())
    cycle([bad, good], state, 1000, alerts)
    assert len(alerts) == 1                 # good still fired despite bad raising


def test_compute_deadline_none_runs_forever():
    assert compute_deadline(None, 1000.0) is None


def test_compute_deadline_from_hours():
    assert compute_deadline(2, 1000.0) == 1000.0 + 7200


def test_compute_deadline_fractional_hours():
    assert compute_deadline(0.5, 0.0) == 1800.0


def test_is_expired_no_deadline():
    assert is_expired(None, 10 ** 12) is False


def test_is_expired_before_deadline():
    assert is_expired(1000.0, 999.0) is False


def test_is_expired_at_or_after_deadline():
    assert is_expired(1000.0, 1000.0) is True
    assert is_expired(1000.0, 1001.0) is True


def test_parse_args_default_hours_is_none():
    assert parse_args([]).hours is None


def test_parse_args_hours():
    assert parse_args(["--hours", "3"]).hours == 3.0


def test_parse_args_rejects_nonpositive_hours():
    import pytest
    with pytest.raises(SystemExit):
        parse_args(["--hours", "0"])


def test_run_cycle_returns_results_for_health_check():
    # The self-healing loop relies on run_cycle returning per-retailer Results
    # so it can detect an all-error (dead browser) cycle.
    state = {}
    ok = FakeChecker(Result(retailer="canon", url="u", in_stock=False, price=879.99))
    boom = spec("bhphoto", Boom())
    results = run_cycle(None, [spec("canon", ok), boom], state, now=1000,
                        alert_fn=lambda *a: None, ceiling=CEILING,
                        realert_seconds=REALERT)
    assert len(results) == 2
    assert any(r.error for r in results)        # the Boom checker errored
    assert not all(r.error for r in results)    # the healthy one did not
