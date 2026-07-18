"""Shared helpers for retailer checkers."""
import re

# First $-prefixed number: optional space, digits with optional thousands
# commas, optional 1-2 decimal places.
_PRICE = re.compile(r"\$\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)")


def parse_price(text):
    """Return the first dollar amount in `text` as a float, or None."""
    if not text:
        return None
    m = _PRICE.search(text)
    if not m:
        return None
    return float(m.group(1).replace(",", ""))
