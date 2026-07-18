from checkers.base import looks_standard
from checkers import canon, bestbuy, bhphoto, target, amazon, adorama


# --- model guard ---------------------------------------------------------

def test_looks_standard_true():
    assert looks_standard("Canon PowerShot G7 X Mark III Digital Camera (Black)") is True


def test_looks_standard_limited_edition():
    assert looks_standard(
        "Canon PowerShot G7 X Mark III (30th Anniversary Graphite Limited Edition)") is False


def test_looks_standard_wrong_model():
    assert looks_standard("Canon PowerShot G7 X Mark II Black") is False


def test_looks_standard_empty():
    assert looks_standard("") is False


# --- JSON-LD availability checkers (canon / bhphoto / adorama) ------------

def test_canon_in_stock():
    assert canon.interpret("InStock", 879.99) == (True, 879.99)


def test_canon_out_of_stock():
    assert canon.interpret("OutOfStock", 879.99) == (False, 879.99)


def test_bhphoto_in_stock():
    assert bhphoto.interpret("InStock", 879.99) == (True, 879.99)


def test_adorama_out_of_stock():
    assert adorama.interpret("OutOfStock", 879.99) == (False, 879.99)


# --- Best Buy (data-button-state or text) --------------------------------

def test_bestbuy_add_to_cart_state():
    assert bestbuy.interpret("ADD_TO_CART", "$879.99") == (True, 879.99)


def test_bestbuy_sold_out_state():
    assert bestbuy.interpret("SOLD_OUT", "$879.99") == (False, 879.99)


def test_bestbuy_button_text():
    assert bestbuy.interpret("Add to Cart", "$879.99") == (True, 879.99)


def test_bestbuy_preselect_no_price():
    assert bestbuy.interpret("PRESELECT", "") == (False, None)


def test_bestbuy_testid_add_to_cart():
    assert bestbuy.interpret("pdp-add-to-cart-6359935", "$879.99") == (True, 879.99)


def test_bestbuy_testid_sold_out():
    assert bestbuy.interpret("pdp-sold-out-6359935", "$879.99") == (False, 879.99)


# --- Target (oos flag + enabled cart) ------------------------------------

def test_target_in_stock():
    assert target.interpret(False, True, "$879.99") == (True, 879.99)


def test_target_out_of_stock_text():
    assert target.interpret(True, False, "$879.99") == (False, 879.99)


def test_target_oos_overrides_enabled_button():
    assert target.interpret(True, True, "$879.99") == (False, 879.99)


def test_target_disabled_button():
    assert target.interpret(False, False, "$879.99") == (False, 879.99)


# --- Amazon (buybox cta + seller passthrough) ----------------------------

def test_amazon_first_party():
    assert amazon.interpret(True, "Amazon.com", "$879.99") == (True, 879.99, "Amazon.com")


def test_amazon_no_buybox():
    assert amazon.interpret(False, "", "") == (False, None, None)


def test_amazon_third_party_passthrough():
    # in_stock/price parsed, seller passed through; qualifies() rejects later.
    assert amazon.interpret(True, "TechDeals LLC", "$1,369.99") == (True, 1369.99, "TechDeals LLC")
