"""Best Buy — JSON-LD availability is unreliable (reports InStock while Sold
Out), and the PDP has ~12 decoy 'Add to cart' buttons for related products.
The real CTA lives in the #a2c / AddToCart container and carries a
data-testid like 'pdp-add-to-cart-<sku>' or 'pdp-sold-out-<sku>'. Price comes
from JSON-LD (reliable number) with a price-block DOM fallback."""
import time

from checkers.base import Result, error_result, looks_standard, extract_jsonld_offer
from checkers.util import parse_price
import config

RETAILER = "bestbuy"


def interpret(cta_signal, price_text):
    """cta_signal: the buy-box button's data-testid ('pdp-add-to-cart-...')
    or its visible text. Hyphens/underscores are normalized so every form of
    'add to cart' matches, while 'sold-out' / 'coming-soon' do not."""
    s = (cta_signal or "").lower().replace("_", " ").replace("-", " ")
    in_stock = "add to cart" in s
    return in_stock, parse_price(price_text)


def check(context, url):
    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=config.NAV_TIMEOUT_MS)
        time.sleep(5)
        box = page.query_selector("#a2c") or \
            page.query_selector('[data-component-name="AddToCart"]')
        signal = ""
        if box:
            btn = box.query_selector("button")
            if btn:
                signal = btn.get_attribute("data-testid") or btn.inner_text() or ""
        # Price: JSON-LD number is reliable; format with $ for the parser.
        offer = extract_jsonld_offer(page)
        if offer and offer["price"] is not None:
            price_text = f"${offer['price']}"
        else:
            pe = page.query_selector('[data-testid="price-block-customer-price"]')
            price_text = pe.inner_text() if pe else ""
        if not signal:
            return error_result(RETAILER, url, "buy-box CTA not found (page layout?)")
        in_stock, price = interpret(signal, price_text)
        return Result(retailer=RETAILER, url=url, in_stock=in_stock, price=price,
                      is_standard_model=looks_standard(page.title()),
                      raw_status=f"cta={signal!r} price={price}")
    except Exception as e:
        return error_result(RETAILER, url, f"{type(e).__name__}: {e}")
    finally:
        page.close()
