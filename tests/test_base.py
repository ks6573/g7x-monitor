from checkers.base import Result, error_result


def test_defaults():
    r = Result(retailer="x", url="u")
    assert r.in_stock is False
    assert r.is_standard_model is True
    assert r.error is None
    assert r.price is None


def test_error_result():
    r = error_result("canon", "u", "timeout")
    assert r.retailer == "canon"
    assert r.error == "timeout"
    assert r.in_stock is False
