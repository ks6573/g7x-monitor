"""The Trigger: decide whether a checker Result is a qualifying MSRP restock."""


def qualifies(result, ceiling):
    """True only when the listing is genuinely buyable at <= MSRP from an
    authorized seller. All clauses must hold:

    - the check succeeded (no error)
    - it is in stock right now
    - it is the standard model (not the Limited Edition)
    - a price was read and it is <= ceiling
    - the seller is authorized (Amazon must be first-party; others inherently so)
    """
    if result.error is not None:
        return False
    if not result.in_stock:
        return False
    if not result.is_standard_model:
        return False
    if result.price is None or result.price > ceiling:
        return False
    if result.retailer == "amazon":
        return "amazon" in (result.seller or "").lower()
    return True
