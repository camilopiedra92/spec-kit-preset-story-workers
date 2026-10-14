"""Largest-remainder allocation."""

from collections.abc import Sequence


def allocate(amount: int, weights: Sequence[int]) -> list[int]:
    if amount == 0:
        return [0] * len(weights)
    total = sum(weights)
    shares = [amount * weight // total for weight in weights]
    remainders = [amount * weight % total for weight in weights]
    # Largest remainder first; on equal remainders the earlier item (sorted is stable).
    order = sorted(range(len(weights)), key=lambda i: -remainders[i])
    for i in order[: amount - sum(shares)]:
        shares[i] += 1
    return shares


def per_unit(amount: int, quantity: int) -> list[int]:
    return allocate(amount, [1] * quantity)
