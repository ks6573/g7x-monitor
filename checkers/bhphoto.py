"""B&H Photo — schema.org JSON-LD is trustworthy here for price + availability."""
import time

from checkers.base import (Result, error_result, looks_standard,
                           extract_jsonld_offer, is_blocked)
import config

RETAILER = "bhphoto"


def interpret(availability, price):
    in_stock = (availability or "").lower() == "instock"
    return in_stock, price


def check(context, url):
    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=config.NAV_TIMEOUT_MS)
        time.sleep(5)
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
