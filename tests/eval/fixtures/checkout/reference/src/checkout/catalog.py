"""The catalog of products."""

from collections.abc import Iterable
from dataclasses import dataclass

from checkout.money import apply_rate

BULK_QUANTITY = 10
BULK_BASIS_POINTS = 9500


class UnknownSku(Exception):
    pass


@dataclass(frozen=True)
class Product:
    sku: str
    unit_price: int
    category: str


class Catalog:
    def __init__(self, products: Iterable[Product]) -> None:
        self._products = {product.sku: product for product in products}

    def get(self, sku: str) -> Product:
        try:
            return self._products[sku]
        except KeyError:
            raise UnknownSku(sku) from None


def line_unit_price(product: Product, quantity: int) -> int:
    """The line's unit price: the bulk price, rounded once per unit, at 10 or more units."""
    if quantity >= BULK_QUANTITY:
        return apply_rate(product.unit_price, BULK_BASIS_POINTS)
    return product.unit_price
