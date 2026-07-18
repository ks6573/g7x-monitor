"""Target — no JSON-LD offer, and the 'Add to cart' button stays present but
disabled when out of stock, so rely on the explicit out-of-stock signal plus
the button's enabled state."""
import re
import time

from checkers.base import Result, error_result, looks_standard, is_blocked
from checkers.util import parse_price
import config

RETAILER = "target"


def interpret(is_out_of_stock, atc_enabled, price_text):
    in_stock = atc_enabled and not is_out_of_stock
    return in_stock, parse_price(price_text)


def check(context, url):
    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=config.NAV_TIMEOUT_MS)
        time.sleep(5)
        if is_blocked(page):
            return error_result(RETAILER, url, "blocked by anti-bot")
        price_el = page.query_selector('[data-test="product-price"]')
        price_text = price_el.inner_text() if price_el else ""
        is_oos = bool(page.query_selector("text=/out of stock/i")) or \
            bool(page.query_selector('button:has-text("Notify me")'))
        atc = page.query_selector('[data-test="shippingButton"]') or \
            page.query_selector('button:has-text("Add to cart")')
        atc_enabled = bool(atc) and not atc.is_disabled()
        in_stock, price = interpret(is_oos, atc_enabled, price_text)
        return Result(retailer=RETAILER, url=url, in_stock=in_stock, price=price,
                      is_standard_model=looks_standard(page.title()),
                      raw_status=f"oos={is_oos} atc_enabled={atc_enabled} price={price}")
    except Exception as e:
        return error_result(RETAILER, url, f"{type(e).__name__}: {e}")
    finally:
        page.close()
