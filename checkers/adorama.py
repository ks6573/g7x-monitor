"""Adorama — anti-bot rejected a cold visit in testing, so warm up on the
homepage first. Its Product JSON-LD lists several offers (bundles/variants),
so select the offer matching the pinned URL, else the lowest-priced 'New'
offer. Best effort: if blocked or no matching offer, return an error."""
import json
import time

from checkers.base import Result, error_result, looks_standard, is_blocked
import config

RETAILER = "adorama"


def interpret(availability, price):
    in_stock = (availability or "").lower() == "instock"
    return in_stock, price


def _to_float(v):
    if v is None:
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def _iter_products(node):
    if isinstance(node, dict):
        t = node.get("@type")
        types = t if isinstance(t, list) else [t]
        if "Product" in types:
            yield node
        for v in node.values():
            yield from _iter_products(v)
    elif isinstance(node, list):
        for v in node:
            yield from _iter_products(v)


def _select_offer(page, product_url):
    base = product_url.split("?")[0]
    for block in page.query_selector_all('script[type="application/ld+json"]'):
        try:
            data = json.loads(block.inner_text())
        except Exception:
            continue
        for prod in _iter_products(data):
            offers = prod.get("offers")
            if isinstance(offers, dict):
                offers = [offers]
            if not isinstance(offers, list):
                continue
            cand = [{
                "price": _to_float(o.get("price") or o.get("lowPrice")),
                "availability": str(o.get("availability") or "").split("/")[-1],
                "condition": str(o.get("itemCondition") or "").split("/")[-1],
                "url": o.get("url") or "",
            } for o in offers if isinstance(o, dict)]
            if not cand:
                continue
            for c in cand:                                    # 1) exact URL match
                if base and base in c["url"]:
                    return c
            new = [c for c in cand if c["condition"].lower().startswith("new") and c["price"]]
            pool = new or [c for c in cand if c["price"]]
            if pool:                                          # 2) lowest 'New' price
                return min(pool, key=lambda c: c["price"])
    return None


def check(context, url):
    page = context.new_page()
    try:
        try:
            page.goto("https://www.adorama.com/", wait_until="domcontentloaded",
                      timeout=config.NAV_TIMEOUT_MS)
            time.sleep(3)
        except Exception:
            pass  # warmup is best-effort
        page.goto(url, wait_until="domcontentloaded", timeout=config.NAV_TIMEOUT_MS)
        time.sleep(5)
        if is_blocked(page):
            return error_result(RETAILER, url, "blocked by anti-bot")
        offer = _select_offer(page, url)
        if not offer:
            return error_result(RETAILER, url, "no matching JSON-LD offer")
        in_stock, price = interpret(offer["availability"], offer["price"])
        return Result(retailer=RETAILER, url=url, in_stock=in_stock, price=price,
                      is_standard_model=looks_standard(page.title()),
                      raw_status=f"availability={offer['availability']} price={price}")
    except Exception as e:
        return error_result(RETAILER, url, f"{type(e).__name__}: {e}")
    finally:
        page.close()
