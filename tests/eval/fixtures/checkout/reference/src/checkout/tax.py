"""Tax per category."""

from collections.abc import Mapping

from checkout.money import apply_rate


class UnknownCategory(Exception):
    pass


class TaxTable:
    def __init__(self, rates: Mapping[str, int]) -> None:
        self._rates = dict(rates)

    def rate(self, category: str) -> int:
        try:
            return self._rates[category]
        except KeyError:
            raise UnknownCategory(category) from None


def line_tax(net: int, basis_points: int) -> int:
    return apply_rate(net, basis_points)
