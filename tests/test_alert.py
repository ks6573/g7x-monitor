from checkers.base import Result
from alert import build_alert


def test_build_alert_fields():
    r = Result(retailer="bestbuy", url="https://buy.example/x",
               in_stock=True, price=879.99)
    title, msg, speak = build_alert(r)
    assert "IN STOCK" in title.upper()
    assert "879.99" in msg
    assert "bestbuy" in msg.lower()
    assert "https://buy.example/x" in msg
    assert "in stock" in speak.lower()
    assert "bestbuy" in speak.lower()


def test_build_alert_handles_missing_price():
    r = Result(retailer="canon", url="u", in_stock=True, price=None)
    title, msg, speak = build_alert(r)
    assert "IN STOCK" in title.upper()
    assert isinstance(speak, str) and speak
