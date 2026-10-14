"""Cent arithmetic."""


def apply_rate(amount: int, basis_points: int) -> int:
    """amount × basis_points / 10000, rounded half-even to the cent."""
    quotient, remainder = divmod(amount * basis_points, 10000)
    twice = 2 * remainder
    if twice > 10000 or (twice == 10000 and quotient % 2 == 1):
        quotient += 1
    return quotient
