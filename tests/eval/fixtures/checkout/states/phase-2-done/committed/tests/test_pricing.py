"""US1-6 and US1-9: the order's net, tax and total; the bulk price."""

import pytest

from checkout.cart import Cart, Receipt, price
from checkout.catalog import Catalog, Product
from checkout.tax import TaxTable

CATALOG = Catalog(
    [
        Product("BOOK", 1050, "books"),
        Product("ATLAS", 1030, "books"),
        Product("PEN", 199, "stationery"),
        Product("TOY", 1000, "toys"),
    ]
)
TAXES = TaxTable({"books": 500, "stationery": 825, "toys": 1000, "groceries": 0})


def priced(*items: tuple[str, int]) -> Receipt:
    cart = Cart(CATALOG)
    for sku, quantity in items:
        cart.add(sku, quantity)
    return price(cart, TAXES)


def test_order_totals_are_the_sums_of_the_lines() -> None:
    receipt = priced(("BOOK", 2), ("PEN", 3), ("TOY", 1))
    assert [line.net for line in receipt.lines] == [2100, 597, 1000]
    assert [line.tax for line in receipt.lines] == [105, 49, 100]
    assert (receipt.net, receipt.tax, receipt.total) == (3697, 254, 3951)


def test_bulk_price_applies_to_the_merged_line() -> None:
    (line,) = priced(("PEN", 9), ("PEN", 1)).lines
    assert (line.quantity, line.unit_price, line.net, line.tax) == (10, 189, 1890, 156)


def test_nine_units_keep_the_catalog_price() -> None:
    (line,) = priced(("PEN", 9)).lines
    assert (line.unit_price, line.net, line.tax) == (199, 1791, 148)


@pytest.mark.parametrize(
    ("sku", "quantity", "unit_price", "net", "tax"),
    [("PEN", 12, 189, 2268, 187), ("ATLAS", 10, 978, 9780, 489)],
)
def test_bulk_price_is_rounded_once_per_unit(
    sku: str, quantity: int, unit_price: int, net: int, tax: int
) -> None:
    (line,) = priced((sku, quantity)).lines
    assert (line.unit_price, line.gross, line.net, line.tax) == (unit_price, net, net, tax)
