from checkers.util import parse_price


def test_basic():
    assert parse_price("$879.99") == 879.99


def test_with_commas():
    assert parse_price("Now $1,299.00") == 1299.00


def test_no_decimals():
    assert parse_price("$880") == 880.0


def test_none():
    assert parse_price(None) is None


def test_garbage():
    assert parse_price("Sold Out") is None


def test_picks_first():
    assert parse_price("$879.99 was $999.99") == 879.99


def test_space_after_dollar():
    assert parse_price("$ 879.99") == 879.99
