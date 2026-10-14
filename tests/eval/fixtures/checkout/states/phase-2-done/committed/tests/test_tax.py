"""US1-4, US1-5, US1-7 and US1-8: per-line half-even tax, a zero price, a 0% category, and a
category without a rate."""

import pytest

from checkout.cart import Cart, Receipt, price
from checkout.catalog import Catalog, Product
from checkout.tax import TaxTable, UnknownCategory

CATALOG = Catalog(
    [
        Product("BOOK", 1050, "books"),
        Product("NOTEBOOK", 1000, "stationery"),
        Product("PEN", 199, "stationery"),
        Product("STICKER", 0, "stationery"),
        Product("BREAD", 350, "groceries"),
        Product("LAMP", 2500, "garden"),
    ]
)
TAXES = TaxTable({"books": 500, "stationery": 825, "toys": 1000, "groceries": 0})


def priced(*items: tuple[str, int]) -> Receipt:
    cart = Cart(CATALOG)
    for sku, quantity in items:
        cart.add(sku, quantity)
    return price(cart, TAXES)


@pytest.mark.parametrize(
    ("sku", "quantity", "net", "tax"),
    [("NOTEBOOK", 1, 1000, 82), ("NOTEBOOK", 3, 3000, 248), ("PEN", 1, 199, 16)],
)
def test_line_tax_is_rounded_half_even(sku: str, quantity: int, net: int, tax: int) -> None:
    (line,) = priced((sku, quantity)).lines
    assert (line.net, line.tax) == (net, tax)


def test_tax_is_rounded_per_line_and_summed() -> None:
    receipt = priced(("NOTEBOOK", 1), ("BOOK", 1))
    assert [line.tax for line in receipt.lines] == [82, 52]
    assert receipt.tax == 134


def test_zero_price_and_zero_rate() -> None:
    receipt = priced(("STICKER", 5), ("BREAD", 4))
    assert [(line.net, line.tax) for line in receipt.lines] == [(0, 0), (1400, 0)]
    assert receipt.total == 1400


def test_category_without_a_rate_is_rejected() -> None:
    with pytest.raises(UnknownCategory):
        priced(("PEN", 1), ("LAMP", 1))
