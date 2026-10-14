"""Promotions: the stacking order, the discount cap and exclusivity."""

from collections.abc import Sequence
from dataclasses import dataclass

from checkout.allocation import allocate
from checkout.catalog import Product, line_unit_price
from checkout.money import apply_rate


@dataclass(frozen=True)
class BuyXGetY:
    sku: str
    buy: int
    get: int
    exclusive: bool = False


@dataclass(frozen=True)
class PercentOff:
    category: str
    basis_points: int
    exclusive: bool = False


@dataclass(frozen=True)
class FixedOff:
    amount: int
    exclusive: bool = False
    min_net: int = 0


Promotion = BuyXGetY | PercentOff | FixedOff


def _stacked(
    items: Sequence[tuple[Product, int]],
    promotions: Sequence[Promotion],
    discount_cap: int | None,
) -> list[int]:
    prices = [line_unit_price(product, quantity) for product, quantity in items]
    nets = [price * quantity for price, (_, quantity) in zip(prices, items, strict=True)]
    # Free units are kept apart: the cap limits only the percentage and fixed amounts.
    free = [0] * len(items)
    discounts = [0] * len(items)

    def take(i: int, amount: int) -> None:
        nets[i] -= amount
        discounts[i] += amount

    for promo in promotions:
        if isinstance(promo, BuyXGetY):
            for i, (product, quantity) in enumerate(items):
                if product.sku == promo.sku:
                    units = quantity // (promo.buy + promo.get) * promo.get
                    nets[i] -= units * prices[i]
                    free[i] += units * prices[i]
    for promo in promotions:
        if isinstance(promo, PercentOff):
            for i, (product, _) in enumerate(items):
                if product.category == promo.category:
                    take(i, apply_rate(nets[i], promo.basis_points))
    for promo in promotions:
        if isinstance(promo, FixedOff):
            current = sum(nets)
            if current < promo.min_net:
                continue
            for i, share in enumerate(allocate(min(promo.amount, current), nets)):
                take(i, share)
    if discount_cap is not None and sum(discounts) > discount_cap:
        discounts = allocate(discount_cap, discounts)
    return [f + d for f, d in zip(free, discounts, strict=True)]


def line_discounts(
    items: Sequence[tuple[Product, int]],
    promotions: Sequence[Promotion],
    discount_cap: int | None = None,
) -> list[int]:
    chosen = _stacked(items, [p for p in promotions if not p.exclusive], discount_cap)
    best_exclusive: list[int] | None = None
    for promo in promotions:
        if promo.exclusive:
            alone = _stacked(items, [promo], discount_cap)
            # Strictly larger: between equal exclusives the one given first stays.
            if best_exclusive is None or sum(alone) > sum(best_exclusive):
                best_exclusive = alone
    # At least as large: on a tie with the non-exclusive pricing the exclusive applies.
    if best_exclusive is not None and sum(best_exclusive) >= sum(chosen):
        chosen = best_exclusive
    return chosen
