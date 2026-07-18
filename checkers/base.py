"""Normalized result type + shared helpers for all retailer checkers.

`Result`, `error_result`, and `looks_standard` are pure (unit-tested).
`extract_jsonld_offer` and `is_blocked` touch a live Playwright page and are
exercised by live smoke runs, not unit tests.
"""
import json
from dataclasses import dataclass


@dataclass
class Result:
    retailer: str
    url: str
    in_stock: bool = False
    price: float | None = None
    seller: str | None = None          # buy-box seller (Amazon); None elsewhere
    is_standard_model: bool = True      # pinned URL guarantees the standard model
    raw_status: str = ""                # human-readable, for logs/debug
    error: str | None = None            # set when the check failed (timeout/captcha/queue)


def error_result(retailer, url, msg):
    """A Result representing a failed check (never counts as in stock)."""
    return Result(retailer=retailer, url=url, in_stock=False,
                  raw_status=msg, error=msg)


def looks_standard(title):
    """Guard against a pinned URL silently redirecting to a different product:
    the standard G7X III, not the 30th Anniversary Limited Edition."""
    t = (title or "").lower()
    if "mark iii" not in t:
        return False
    if "anniversary" in t or "limited edition" in t:
        return False
    return True


# --- live-page helpers (not unit-tested) ----------------------------------

def _find_offer(node):
    if isinstance(node, dict):
        lower = {k.lower(): k for k in node}
        if "price" in lower or "availability" in lower:
            raw_price = node.get(lower.get("price", ""))
            avail = node.get(lower.get("availability", "")) or ""
            price = None
            if raw_price is not None:
                try:
                    price = float(str(raw_price).replace(",", ""))
                except ValueError:
                    price = None
            return {"price": price, "availability": str(avail).split("/")[-1] or None}
        for v in node.values():
            found = _find_offer(v)
            if found:
                return found
    elif isinstance(node, list):
        for v in node:
            found = _find_offer(v)
            if found:
                return found
    return None


def extract_jsonld_offer(page):
    """First schema.org Offer with price/availability, or None.
    availability is normalized to the bare token, e.g. 'InStock'."""
    for block in page.query_selector_all('script[type="application/ld+json"]'):
        try:
            data = json.loads(block.inner_text())
        except Exception:
            continue
        found = _find_offer(data)
        if found:
            return found
    return None


def is_blocked(page):
    """True when the page is an anti-bot denial rather than the product."""
    try:
        title = (page.title() or "").lower()
    except Exception:
        title = ""
    return any(s in title for s in (
        "access denied", "has been denied", "pardon our interruption",
        "robot", "are you a human"))
