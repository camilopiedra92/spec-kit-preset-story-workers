"""Promotions: the stacking order, the discount cap and exclusivity."""

from collections.abc import Sequence
from dataclasses import dataclass

from checkout.allocation import allocate
from checkout.catalog import Product
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


Promotion = BuyXGetY | PercentOff | FixedOff


def _stacked(
    items: Sequence[tuple[Product, int]],
    promotions: Sequence[Promotion],
    discount_cap: int | None,
) -> list[int]:
    nets = [product.unit_price * quantity for product, quantity in items]
    discounts = [0] * len(items)

    def take(i: int, amount: int) -> None:
        nets[i] -= amount
        discounts[i] += amount

    for promo in promotions:
        if isinstance(promo, BuyXGetY):
            for i, (product, quantity) in enumerate(items):
                if product.sku == promo.sku:
                    free = quantity // (promo.buy + promo.get) * promo.get
                    take(i, free * product.unit_price)
    for promo in promotions:
        if isinstance(promo, PercentOff):
            for i, (product, _) in enumerate(items):
                if product.category == promo.category:
                    take(i, apply_rate(nets[i], promo.basis_points))
    for promo in promotions:
        if isinstance(promo, FixedOff):
            amount = min(promo.amount, sum(nets))
            for i, share in enumerate(allocate(amount, nets)):
                take(i, share)
    if discount_cap is not None and sum(discounts) > discount_cap:
        discounts = allocate(discount_cap, discounts)
    return discounts


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
