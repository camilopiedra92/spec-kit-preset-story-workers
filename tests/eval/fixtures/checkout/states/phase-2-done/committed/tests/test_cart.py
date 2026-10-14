"""US1-2 and US1-3: quantities, and adding a SKU already in the cart."""

import pytest

from checkout.cart import Cart, InvalidQuantity
from checkout.catalog import Catalog, Product


def new_cart() -> Cart:
    return Cart(Catalog([Product("PEN", 199, "stationery"), Product("BOOK", 1050, "books")]))


def contents(cart: Cart) -> list[tuple[str, int]]:
    return [(line.product.sku, line.quantity) for line in cart.lines]


@pytest.mark.parametrize("quantity", [0, 100, -1])
def test_quantity_outside_1_to_99_is_rejected(quantity: int) -> None:
    cart = new_cart()
    with pytest.raises(InvalidQuantity):
        cart.add("PEN", quantity)
    assert contents(cart) == []


@pytest.mark.parametrize("quantity", [1, 99])
def test_quantity_1_and_99_are_accepted(quantity: int) -> None:
    cart = new_cart()
    cart.add("PEN", quantity)
    assert contents(cart) == [("PEN", quantity)]


def test_same_sku_adds_to_its_line_which_keeps_its_place() -> None:
    cart = new_cart()
    cart.add("PEN", 2)
    cart.add("BOOK", 1)
    cart.add("PEN", 3)
    assert contents(cart) == [("PEN", 5), ("BOOK", 1)]


def test_merge_past_99_is_rejected_and_the_line_is_unchanged() -> None:
    cart = new_cart()
    cart.add("PEN", 2)
    cart.add("BOOK", 1)
    cart.add("PEN", 3)
    with pytest.raises(InvalidQuantity):
        cart.add("PEN", 95)
    assert contents(cart) == [("PEN", 5), ("BOOK", 1)]
