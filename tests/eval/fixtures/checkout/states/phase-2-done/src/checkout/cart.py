"""The cart and its pricing."""

from collections.abc import Sequence
from dataclasses import dataclass

from checkout.catalog import Catalog, Product, line_unit_price
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
    promotions: Sequence[object] = (),
    discount_cap: int | None = None,
) -> Receipt:
    # plan.md's signature, so callers need not change when promotions arrive (User Story 2,
    # T021); until then a promotion or a cap is refused rather than silently ignored.
    if promotions or discount_cap is not None:
        raise NotImplementedError("promotions and the discount cap arrive with User Story 2")
    lines = []
    for line in cart.lines:
        unit_price = line_unit_price(line.product, line.quantity)
        gross = unit_price * line.quantity
        discount = 0
        net = gross - discount
        lines.append(
            PricedLine(
                sku=line.product.sku,
                quantity=line.quantity,
                unit_price=unit_price,
                gross=gross,
                discount=discount,
                net=net,
                tax=line_tax(net, taxes.rate(line.product.category)),
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
