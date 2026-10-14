"""Returns against a priced order."""

from dataclasses import dataclass

from checkout.cart import InvalidQuantity, PricedLine, Receipt
from checkout.catalog import UnknownSku


class OverReturn(ValueError):
    pass


@dataclass(frozen=True)
class Refund:
    sku: str
    quantity: int
    net: int
    tax: int
    total: int


class Order:
    def __init__(self, receipt: Receipt) -> None:
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
        return Refund(sku=sku, quantity=quantity, net=net, tax=tax, total=net + tax)
