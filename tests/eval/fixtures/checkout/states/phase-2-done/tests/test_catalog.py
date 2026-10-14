"""US1-1: an unknown SKU."""

import pytest

from checkout.cart import Cart
from checkout.catalog import Catalog, Product, UnknownSku


def test_unknown_sku_is_rejected_and_the_cart_stays_empty() -> None:
    cart = Cart(Catalog([Product("PEN", 199, "stationery")]))
    with pytest.raises(UnknownSku):
        cart.add("NOPE", 1)
    assert cart.lines == ()
