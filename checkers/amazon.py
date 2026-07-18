"""Amazon — best-effort. Only a first-party buy box counts: an Add to Cart /
Buy Now button whose seller is Amazon. 'See All Buying Options' (3rd-party
only) is NOT in stock. Price is scoped to the buy box so alternative-item
prices elsewhere on the page can't leak in. CAPTCHA/robot pages -> error."""
import time

from checkers.base import Result, error_result, looks_standard, is_blocked
from checkers.util import parse_price
import config

RETAILER = "amazon"

_PRICE_SEL = ("#corePriceDisplay_desktop_feature_div .a-offscreen, "
              "#corePrice_feature_div .a-offscreen, "
              "#price_inside_buybox")
_SELLER_SEL = "#sellerProfileTriggerId, #merchant-info"


def interpret(has_buybox_cta, seller_text, price_text):
    """Returns (in_stock, price, seller). qualifies() enforces seller==Amazon."""
    in_stock = bool(has_buybox_cta)
    return in_stock, parse_price(price_text), (seller_text or None)


def check(context, url):
    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=config.NAV_TIMEOUT_MS)
        time.sleep(5)
        if is_blocked(page):
            return error_result(RETAILER, url, "blocked / captcha")
        cta = page.query_selector("#add-to-cart-button, #buy-now-button")
        seller_el = page.query_selector(_SELLER_SEL)
        seller_text = seller_el.inner_text() if seller_el else ""
        price_el = page.query_selector(_PRICE_SEL)
        price_text = price_el.inner_text() if price_el else ""
        in_stock, price, seller = interpret(bool(cta), seller_text, price_text)
        return Result(retailer=RETAILER, url=url, in_stock=in_stock, price=price,
                      seller=seller, is_standard_model=looks_standard(page.title()),
                      raw_status=f"buybox_cta={bool(cta)} seller={seller!r} price={price}")
    except Exception as e:
        return error_result(RETAILER, url, f"{type(e).__name__}: {e}")
    finally:
        page.close()
