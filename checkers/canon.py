"""Canon USA — behind Akamai + Queue-It. Uses schema.org JSON-LD (trustworthy
here), and treats a Queue-It redirect as a possible-drop signal, never a hit."""
import time

from checkers.base import (Result, error_result, looks_standard,
                           extract_jsonld_offer, is_blocked)
import config

RETAILER = "canon"


def interpret(availability, price):
    """availability: schema.org token ('InStock' / 'OutOfStock' / ...)."""
    in_stock = (availability or "").lower() == "instock"
    return in_stock, price


def check(context, url):
    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=config.NAV_TIMEOUT_MS)
        time.sleep(5)
        if "queue" in page.url.lower():
            return error_result(RETAILER, url, "queue-it waiting room (possible drop)")
        if is_blocked(page):
            return error_result(RETAILER, url, "blocked by anti-bot")
        offer = extract_jsonld_offer(page)
        if not offer:
            return error_result(RETAILER, url, "no JSON-LD offer found")
        in_stock, price = interpret(offer["availability"], offer["price"])
        return Result(retailer=RETAILER, url=url, in_stock=in_stock, price=price,
                      is_standard_model=looks_standard(page.title()),
                      raw_status=f"availability={offer['availability']} price={price}")
    except Exception as e:
        return error_result(RETAILER, url, f"{type(e).__name__}: {e}")
    finally:
        page.close()
