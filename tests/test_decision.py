from checkers.base import Result
from decision import qualifies

CEILING = 879.99


def R(**kw):
    retailer = kw.pop("retailer", "bestbuy")
    return Result(retailer=retailer, url="u", **kw)


def q(**kw):
    return qualifies(R(**kw), CEILING)


def test_qualifies_at_msrp():
    assert q(in_stock=True, price=879.99) is True


def test_qualifies_below_msrp():
    assert q(in_stock=True, price=799.00) is True


def test_price_above_ceiling():
    assert q(in_stock=True, price=899.00) is False


def test_out_of_stock():
    assert q(in_stock=False, price=800.0) is False


def test_no_price():
    assert q(in_stock=True, price=None) is False


def test_error_blocks():
    assert q(in_stock=True, price=800.0, error="queue") is False


def test_limited_edition():
    assert q(in_stock=True, price=800.0, is_standard_model=False) is False


def test_amazon_third_party_seller():
    assert q(retailer="amazon", in_stock=True, price=850.0, seller="TechDeals LLC") is False


def test_amazon_first_party_seller():
    assert q(retailer="amazon", in_stock=True, price=850.0, seller="Amazon.com") is True


def test_amazon_missing_seller():
    assert q(retailer="amazon", in_stock=True, price=850.0, seller=None) is False
