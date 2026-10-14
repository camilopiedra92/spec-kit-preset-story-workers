"""The catalog of products."""

from collections.abc import Iterable
from dataclasses import dataclass


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
