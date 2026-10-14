"""The cart and its pricing."""

from collections.abc import Sequence
from dataclasses import dataclass

from checkout.allocation import per_unit
from checkout.catalog import Catalog, Product, line_unit_price
from checkout.promotions import Promotion, line_discounts
from checkout.tax import TaxTable, line_tax

MAX_QUANTITY = 99


class InvalidQuantity(ValueError):
    pass


@dataclass(frozen=True)
class CartLine:
    product: Product
    quantity: int


class Cart:
    def __init__(self, catalog: Catalog) -> None:
        self._catalog = catalog
        self._lines: list[CartLine] = []

    def add(self, sku: str, quantity: int) -> None:
        product = self._catalog.get(sku)
        for i, line in enumerate(self._lines):
            if line.product.sku == sku:
                self._lines[i] = CartLine(product, _checked(line.quantity + quantity))
                return
        self._lines.append(CartLine(product, _checked(quantity)))

    @property
    def lines(self) -> tuple[CartLine, ...]:
        return tuple(self._lines)


def _checked(quantity: int) -> int:
    if not 1 <= quantity <= MAX_QUANTITY:
        raise InvalidQuantity(quantity)
    return quantity


@dataclass(frozen=True)
class PricedLine:
    sku: str
    quantity: int
    unit_price: int
    gross: int
    discount: int
    net: int
    tax: int
    unit_nets: tuple[int, ...]
    unit_taxes: tuple[int, ...]


@dataclass(frozen=True)
class Receipt:
    lines: tuple[PricedLine, ...]
    gross: int
    discount: int
    net: int
    tax: int
    total: int


def price(
    cart: Cart,
    taxes: TaxTable,
    promotions: Sequence[Promotion] = (),
    discount_cap: int | None = None,
) -> Receipt:
    items = [(line.product, line.quantity) for line in cart.lines]
    discounts = line_discounts(items, promotions, discount_cap)
    lines = []
    for (product, quantity), discount in zip(items, discounts, strict=True):
        unit_price = line_unit_price(product, quantity)
        gross = unit_price * quantity
        net = gross - discount
        tax = line_tax(net, taxes.rate(product.category))
        lines.append(
            PricedLine(
                sku=product.sku,
                quantity=quantity,
                unit_price=unit_price,
                gross=gross,
                discount=discount,
                net=net,
                tax=tax,
                unit_nets=tuple(per_unit(net, quantity)),
                unit_taxes=tuple(per_unit(tax, quantity)),
            )
        )
    net = sum(line.net for line in lines)
    tax = sum(line.tax for line in lines)
    return Receipt(
        lines=tuple(lines),
        gross=sum(line.gross for line in lines),
        discount=sum(line.discount for line in lines),
        net=net,
        tax=tax,
        total=net + tax,
    )
