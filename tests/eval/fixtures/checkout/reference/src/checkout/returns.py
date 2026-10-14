"""Returns against a priced order."""

from dataclasses import dataclass

from checkout.cart import InvalidQuantity, PricedLine, Receipt
from checkout.catalog import UnknownSku
from checkout.money import apply_rate


class OverReturn(ValueError):
    pass


@dataclass(frozen=True)
class Refund:
    sku: str
    quantity: int
    net: int
    tax: int
    fee: int
    total: int


class Order:
    def __init__(
        self, receipt: Receipt, fee_basis_points: int = 0, fee_cap: int | None = None
    ) -> None:
        self._fee_basis_points = fee_basis_points
        self._fee_cap = fee_cap
        self._fees = 0
        self._lines: dict[str, PricedLine] = {line.sku: line for line in receipt.lines}
        self._returned: dict[str, int] = dict.fromkeys(self._lines, 0)

    def return_units(self, sku: str, quantity: int) -> Refund:
        if sku not in self._lines:
            raise UnknownSku(sku)
        if quantity < 1:
            raise InvalidQuantity(quantity)
        line = self._lines[sku]
        start = self._returned[sku]
        if start + quantity > line.quantity:
            raise OverReturn(f"{quantity} of {sku}, {line.quantity - start} remain")
        self._returned[sku] = start + quantity
        net = sum(line.unit_nets[start : start + quantity])
        tax = sum(line.unit_taxes[start : start + quantity])
        # Rounded once on the refund's net, then limited by what the order's cap has left.
        fee = apply_rate(net, self._fee_basis_points)
        if self._fee_cap is not None:
            fee = min(fee, self._fee_cap - self._fees)
        self._fees += fee
        return Refund(sku=sku, quantity=quantity, net=net, tax=tax, fee=fee, total=net + tax - fee)
