"""Held-out acceptance tests: at least one per acceptance scenario of the fixture's spec.

Never in the fixture: run.sh copies them into the scratch repository only after
the agent has finished, so no arm sees them, and every arm is judged by them.
Each test names its scenario (US<n>-<m>) and quotes the spec text its expected
values follow from; they use only the interface plan.md fixes.
"""

import importlib
from types import ModuleType
from typing import Any

import pytest

# The spec's catalog and tax table ("Conventions used in every scenario").
CATALOG = [
    ("BOOK", 1050, "books"),
    ("ATLAS", 1030, "books"),
    ("JOURNAL", 1000, "books"),
    ("NOTEBOOK", 1000, "stationery"),
    ("PEN", 199, "stationery"),
    ("STICKER", 0, "stationery"),
    ("TOY", 1000, "toys"),
    ("BREAD", 350, "groceries"),
    ("LAMP", 2500, "garden"),
]
RATES = {"books": 500, "stationery": 825, "toys": 1000, "groceries": 0}


class Modules:
    """`co.<module>` imports checkout.<module> when a test first touches it."""

    def __getattr__(self, name: str) -> ModuleType:
        return importlib.import_module(f"checkout.{name}")


@pytest.fixture
def co() -> Modules:
    # Imported lazily, per use, not at the top or all at once: a missing module
    # or name then fails only the tests that use it, and the total stays the
    # number of tests written (seen: without returns.py, only US3's 10 fail).
    return Modules()


def new_cart(co: Modules) -> Any:
    products = [co.catalog.Product(sku, price, cat) for sku, price, cat in CATALOG]
    return co.cart.Cart(co.catalog.Catalog(products))


def cart_with(co: Modules, *items: tuple[str, int]) -> Any:
    cart = new_cart(co)
    for sku, quantity in items:
        cart.add(sku, quantity)
    return cart


def priced(
    co: Modules,
    items: list[tuple[str, int]],
    promotions: tuple[Any, ...] = (),
    discount_cap: int | None = None,
) -> Any:
    taxes = co.tax.TaxTable(RATES)
    cart = cart_with(co, *items)
    return co.cart.price(cart, taxes, promotions=promotions, discount_cap=discount_cap)


def line_amounts(receipt: Any, field: str) -> list[int]:
    return [getattr(line, field) for line in receipt.lines]


def cart_lines(cart: Any) -> list[tuple[str, int]]:
    return [(line.product.sku, line.quantity) for line in cart.lines]


# User Story 1 - Price a cart with tax


def test_us1_1_unknown_sku_rejected(co: Modules) -> None:
    """US1-1: "When SKU `NOPE` (not in the catalog) is added, Then the addition is rejected
    with `UnknownSku` and the cart stays empty."
    """
    cart = new_cart(co)
    with pytest.raises(co.catalog.UnknownSku):
        cart.add("NOPE", 1)
    assert cart_lines(cart) == []


@pytest.mark.parametrize("quantity", [0, 100, -1])
def test_us1_2_quantity_outside_1_to_99_rejected(co: Modules, quantity: int) -> None:
    """US1-2: "When `PEN` is added with quantity 0, 100 or -1, Then each addition is rejected
    with `InvalidQuantity` and the cart stays empty"
    """
    cart = new_cart(co)
    with pytest.raises(co.cart.InvalidQuantity):
        cart.add("PEN", quantity)
    assert cart_lines(cart) == []


@pytest.mark.parametrize("quantity", [1, 99])
def test_us1_2_quantity_1_and_99_accepted(co: Modules, quantity: int) -> None:
    """US1-2: "quantities 1 and 99 are accepted: a line's quantity is a whole number from 1 to
    99."
    """
    assert cart_lines(cart_with(co, ("PEN", quantity))) == [("PEN", quantity)]


def test_us1_3_same_sku_adds_to_its_line(co: Modules) -> None:
    """US1-3: "When `PEN` ×2, then `BOOK` ×1, then `PEN` ×3 are added, Then the cart has two
    lines, `PEN` ×5 then `BOOK` ×1: adding a SKU already in the cart adds to that line's quantity
    and the line keeps its place, and lines are ordered by when their SKU was first added."
    """
    cart = cart_with(co, ("PEN", 2), ("BOOK", 1), ("PEN", 3))
    assert cart_lines(cart) == [("PEN", 5), ("BOOK", 1)]


def test_us1_3_merge_past_99_rejected(co: Modules) -> None:
    """US1-3: "When `PEN` ×95 is then added, Then it is rejected with `InvalidQuantity`, because
    the line would hold 100, and `PEN` stays at 5."
    """
    cart = cart_with(co, ("PEN", 2), ("BOOK", 1), ("PEN", 3))
    with pytest.raises(co.cart.InvalidQuantity):
        cart.add("PEN", 95)
    assert cart_lines(cart) == [("PEN", 5), ("BOOK", 1)]


@pytest.mark.parametrize(
    ("sku", "quantity", "net", "tax"),
    [("NOTEBOOK", 1, 1000, 82), ("NOTEBOOK", 3, 3000, 248), ("PEN", 1, 199, 16)],
)
def test_us1_4_line_tax_rounded_half_even(
    co: Modules, sku: str, quantity: int, net: int, tax: int
) -> None:
    """US1-4: "Given a cart with `NOTEBOOK` ×1, When it is priced, Then the line's net is 1000
    (unit price × quantity) and its tax is 82 (8.25% of 1000 is 82.5, rounded half-even); given
    `NOTEBOOK` ×3 instead, the net is 3000 and the tax is 248 (247.5 rounded half-even); given
    `PEN` ×1, the net is 199 and the tax is 16 (16.4175 rounded)."
    """
    receipt = priced(co, [(sku, quantity)])
    assert line_amounts(receipt, "net") == [net]
    assert line_amounts(receipt, "tax") == [tax]


def test_us1_5_tax_rounded_per_line(co: Modules) -> None:
    """US1-5: "Then the line taxes are 82 and 52 (52.5 rounded half-even) and the order's tax is
    134: tax is rounded per line and the order's tax is the sum of the rounded line taxes"
    """
    receipt = priced(co, [("NOTEBOOK", 1), ("BOOK", 1)])
    assert line_amounts(receipt, "tax") == [82, 52]
    assert receipt.tax == 134


def test_us1_6_order_totals(co: Modules) -> None:
    """US1-6: "Then the line nets are 2100, 597 and 1000, the line taxes 105, 49 and 100, and the
    order's net is 3697, its tax 254 and its total 3951"
    """
    receipt = priced(co, [("BOOK", 2), ("PEN", 3), ("TOY", 1)])
    assert line_amounts(receipt, "net") == [2100, 597, 1000]
    assert line_amounts(receipt, "tax") == [105, 49, 100]
    assert (receipt.net, receipt.tax, receipt.total) == (3697, 254, 3951)


def test_us1_7_zero_price_and_zero_rate(co: Modules) -> None:
    """US1-7: "Then the `STICKER` line's net and tax are 0, the `BREAD` line's net is 1400 and
    its tax 0 (a 0% category), and the order's total is 1400."
    """
    receipt = priced(co, [("STICKER", 5), ("BREAD", 4)])
    assert line_amounts(receipt, "net") == [0, 1400]
    assert line_amounts(receipt, "tax") == [0, 0]
    assert receipt.total == 1400


def test_us1_8_category_without_rate_rejected(co: Modules) -> None:
    """US1-8: "Given a cart with `PEN` ×1 and `LAMP` ×1, When it is priced, Then pricing is
    rejected with `UnknownCategory`"
    """
    with pytest.raises(co.tax.UnknownCategory):
        priced(co, [("PEN", 1), ("LAMP", 1)])


# User Story 2 - Promotions


@pytest.mark.parametrize(("quantity", "discount"), [(5, 1000), (6, 2000), (2, 0)])
def test_us2_1_buy_x_get_y(co: Modules, quantity: int, discount: int) -> None:
    """US2-1: "Given buy 2 get 1 free on `TOY`, When a cart with `TOY` ×5 is priced, Then the
    line's discount is 1000 (one free unit: of every 3 units, 1 is free, and 5 units hold one
    group of 3), its net 4000 and its tax 400; with `TOY` ×6 the discount is 2000; with `TOY` ×2
    it is 0."
    """
    promo = co.promotions.BuyXGetY("TOY", 2, 1)
    receipt = priced(co, [("TOY", quantity)], (promo,))
    assert line_amounts(receipt, "discount") == [discount]
    if quantity == 5:
        assert line_amounts(receipt, "net") == [4000]
        assert line_amounts(receipt, "tax") == [400]


def test_us2_1_free_unit_at_zero_price(co: Modules) -> None:
    """US2-1: "Given buy 1 get 1 free on `STICKER`, When a cart with `STICKER` ×4 is priced, Then
    two units are free and the discount is 0, since a free unit at zero price is worth 0."
    """
    receipt = priced(co, [("STICKER", 4)], (co.promotions.BuyXGetY("STICKER", 1, 1),))
    assert line_amounts(receipt, "discount") == [0]


def test_us2_2_percentage_per_line_half_even(co: Modules) -> None:
    """US2-2: "Given 15% off `books`, When a cart with `BOOK` ×1, `ATLAS` ×1 and `TOY` ×1 is
    priced, Then the `BOOK` discount is 158 (157.5 rounded half-even) with net 892 and tax 45, the
    `ATLAS` discount is 154 (154.5 rounded half-even) with net 876 and tax 44, and `TOY`, not a
    book, has discount 0 and tax 100."
    """
    promo = co.promotions.PercentOff("books", 1500)
    receipt = priced(co, [("BOOK", 1), ("ATLAS", 1), ("TOY", 1)], (promo,))
    assert line_amounts(receipt, "discount") == [158, 154, 0]
    assert line_amounts(receipt, "net") == [892, 876, 1000]
    assert line_amounts(receipt, "tax") == [45, 44, 100]


def test_us2_2_percentages_compound_in_given_order(co: Modules) -> None:
    """US2-2: "Given 10% off `toys` and then 20% off `toys`, When a cart with `TOY` ×1 is priced,
    Then the discount is 280 and the net 720: the second percentage applies to the 900 the first
    left."
    """
    promos = (co.promotions.PercentOff("toys", 1000), co.promotions.PercentOff("toys", 2000))
    receipt = priced(co, [("TOY", 1)], promos)
    assert line_amounts(receipt, "discount") == [280]
    assert line_amounts(receipt, "net") == [720]


def test_us2_3_stacking_order(co: Modules) -> None:
    """US2-3: "Given buy 2 get 1 free on `TOY`, 10% off `toys` and 500 off the order, When a cart
    with `TOY` ×3 is priced, Then the free unit takes 1000 (net 2000), the percentage 200 (net
    1800) and the fixed amount 500, so the discount is 1700, the net 1300, the tax 130 and the
    total 1430"
    """
    p = co.promotions
    promos = (p.BuyXGetY("TOY", 2, 1), p.PercentOff("toys", 1000), p.FixedOff(500))
    receipt = priced(co, [("TOY", 3)], promos)
    assert (receipt.discount, receipt.net, receipt.tax, receipt.total) == (1700, 1300, 130, 1430)


def test_us2_3_stacking_order_ignores_given_order(co: Modules) -> None:
    """US2-3: "the same three promotions given in the reverse order price the same, since the
    stacking order does not depend on the order they are given in."
    """
    p = co.promotions
    promos = (p.FixedOff(500), p.PercentOff("toys", 1000), p.BuyXGetY("TOY", 2, 1))
    receipt = priced(co, [("TOY", 3)], promos)
    assert (receipt.discount, receipt.net, receipt.tax, receipt.total) == (1700, 1300, 130, 1430)


def test_us2_4_fixed_allocated_by_largest_remainder(co: Modules) -> None:
    """US2-4: "Given 100 off the order, When a cart with `TOY` ×1, `STICKER` ×3, `BOOK` ×2 and
    `PEN` ×5 (current nets 1000, 0, 2100 and 995) is priced, Then the line discounts are 25, 0, 51
    and 24 (...), the line nets 975, 0, 2049 and 971, the line taxes 98, 0, 102 and 80, and the
    order's total 4275: tax is computed on the discounted line nets, and a zero-priced line gets
    no share."
    """
    items = [("TOY", 1), ("STICKER", 3), ("BOOK", 2), ("PEN", 5)]
    receipt = priced(co, items, (co.promotions.FixedOff(100),))
    assert line_amounts(receipt, "discount") == [25, 0, 51, 24]
    assert line_amounts(receipt, "net") == [975, 0, 2049, 971]
    assert line_amounts(receipt, "tax") == [98, 0, 102, 80]
    assert receipt.total == 4275


def test_us2_4_fixed_never_below_zero(co: Modules) -> None:
    """US2-4: "Given 5000 off the order, When a cart with `TOY` ×1 and `BOOK` ×1 is priced, Then
    the discount is 2050 (1000 and 1050), every net and tax is 0 and the total is 0"
    """
    receipt = priced(co, [("TOY", 1), ("BOOK", 1)], (co.promotions.FixedOff(5000),))
    assert receipt.discount == 2050
    assert line_amounts(receipt, "discount") == [1000, 1050]
    assert line_amounts(receipt, "net") == [0, 0]
    assert line_amounts(receipt, "tax") == [0, 0]
    assert receipt.total == 0


def test_us2_5_equal_remainders_two_lines(co: Modules) -> None:
    """US2-5: "Given 1 off the order, When a cart with `TOY` ×1 and `JOURNAL` ×1 (equal nets) is
    priced, Then `TOY`, the earlier line, gets the cent: discounts 1 and 0."
    """
    receipt = priced(co, [("TOY", 1), ("JOURNAL", 1)], (co.promotions.FixedOff(1),))
    assert line_amounts(receipt, "discount") == [1, 0]


def test_us2_5_equal_remainders_three_lines(co: Modules) -> None:
    """US2-5: "Given 100 off the order, When a cart with `NOTEBOOK` ×1, `TOY` ×1 and `JOURNAL` ×1
    is priced, Then the discounts are 34, 33 and 33: equal remainders, so the leftover cent goes
    to the earliest line."
    """
    items = [("NOTEBOOK", 1), ("TOY", 1), ("JOURNAL", 1)]
    receipt = priced(co, items, (co.promotions.FixedOff(100),))
    assert line_amounts(receipt, "discount") == [34, 33, 33]


def cap_promotions(co: Modules) -> tuple[Any, ...]:
    p = co.promotions
    return (p.PercentOff("books", 2000), p.PercentOff("toys", 1000), p.FixedOff(200))


def test_us2_6_cap_reached(co: Modules) -> None:
    """US2-6: "Given 20% off `books`, 10% off `toys`, 200 off the order and a discount cap of 800,
    When a cart with `JOURNAL` ×3 and `TOY` ×1 is priced, Then the discounts before the cap are 745
    and 155 (...), 900 in all, more than the cap; the cap of
    800 is allocated over 745 and 155, giving discounts 662 and 138, nets 2338 and 862, taxes 117
    and 86, and an order net of 3200, tax 203 and total 3403."
    """
    receipt = priced(co, [("JOURNAL", 3), ("TOY", 1)], cap_promotions(co), 800)
    assert line_amounts(receipt, "discount") == [662, 138]
    assert line_amounts(receipt, "net") == [2338, 862]
    assert line_amounts(receipt, "tax") == [117, 86]
    assert (receipt.net, receipt.tax, receipt.total) == (3200, 203, 3403)


def test_us2_6_cap_not_reached(co: Modules) -> None:
    """US2-6: "With a cap of 1000 instead, the cap is not reached: discounts 745 and 155, nets
    2255 and 845, taxes 113 (112.75 rounded) and 84 (84.5 rounded half-even), total 3297."
    """
    receipt = priced(co, [("JOURNAL", 3), ("TOY", 1)], cap_promotions(co), 1000)
    assert line_amounts(receipt, "discount") == [745, 155]
    assert line_amounts(receipt, "net") == [2255, 845]
    assert line_amounts(receipt, "tax") == [113, 84]
    assert receipt.total == 3297


def test_us2_7_larger_exclusive_wins(co: Modules) -> None:
    """US2-7: "Given an exclusive 30% off `toys` and the non-exclusive 10% off `toys` and 100 off
    the order, When a cart with `TOY` ×2 is priced, Then the exclusive pricing (discount 600) beats
    the non-exclusive one (200 + 100 = 300): discount 600, net 1400, tax 140, total 1540."
    """
    p = co.promotions
    promos = (
        p.PercentOff("toys", 3000, exclusive=True),
        p.PercentOff("toys", 1000),
        p.FixedOff(100),
    )
    receipt = priced(co, [("TOY", 2)], promos)
    assert (receipt.discount, receipt.net, receipt.tax, receipt.total) == (600, 1400, 140, 1540)


def test_us2_7_larger_non_exclusive_wins(co: Modules) -> None:
    """US2-7: "With an exclusive 5% off `toys` (discount 100) instead, the non-exclusive pricing
    applies: discount 300, net 1700, tax 170."
    """
    p = co.promotions
    promos = (
        p.PercentOff("toys", 500, exclusive=True),
        p.PercentOff("toys", 1000),
        p.FixedOff(100),
    )
    receipt = priced(co, [("TOY", 2)], promos)
    assert (receipt.discount, receipt.net, receipt.tax) == (300, 1700, 170)


def test_us2_7_best_exclusive_applies(co: Modules) -> None:
    """US2-7: "With both exclusives, the 30% (600) is the best exclusive and applies." """
    p = co.promotions
    promos = (
        p.PercentOff("toys", 500, exclusive=True),
        p.PercentOff("toys", 3000, exclusive=True),
        p.PercentOff("toys", 1000),
        p.FixedOff(100),
    )
    receipt = priced(co, [("TOY", 2)], promos)
    assert (receipt.discount, receipt.net) == (600, 1400)


def test_us2_7_tied_exclusives_first_given_applies(co: Modules) -> None:
    """US2-7: "Given an exclusive 600 off the order given first and an exclusive 30% off `toys`
    given second, When a cart with `TOY` ×2 and `JOURNAL` ×1 is priced, Then both take 600, so the
    one given first applies: discounts 400 and 200; given in the other order, the 30% applies:
    discounts 600 and 0."
    """
    p = co.promotions
    fixed = p.FixedOff(600, exclusive=True)
    percent = p.PercentOff("toys", 3000, exclusive=True)
    items = [("TOY", 2), ("JOURNAL", 1)]
    assert line_amounts(priced(co, items, (fixed, percent)), "discount") == [400, 200]
    assert line_amounts(priced(co, items, (percent, fixed)), "discount") == [600, 0]


@pytest.mark.parametrize("exclusive_first", [True, False])
def test_us2_8_tie_exclusive_applies(co: Modules, exclusive_first: bool) -> None:
    """US2-8: "Given an exclusive 10% off `toys` and a non-exclusive 100 off the order, When a
    cart with `TOY` ×1 and `JOURNAL` ×1 is priced, Then both pricings discount 100, so the
    exclusive one applies: discounts 100 and 0, taxes 90 and 50, total 2040." The given order is
    not part of this tie-break: "When an exclusive pricing and the non-exclusive pricing give
    equal total discounts, the exclusive one applies".
    """
    exclusive = co.promotions.PercentOff("toys", 1000, exclusive=True)
    fixed = co.promotions.FixedOff(100)
    promos = (exclusive, fixed) if exclusive_first else (fixed, exclusive)
    receipt = priced(co, [("TOY", 1), ("JOURNAL", 1)], promos)
    assert line_amounts(receipt, "discount") == [100, 0]
    assert line_amounts(receipt, "tax") == [90, 50]
    assert receipt.total == 2040


def test_us2_8_tie_after_cap_exclusive_applies(co: Modules) -> None:
    """US2-8: "Given an exclusive 30% off `toys`, a non-exclusive 400 off the order and a discount
    cap of 300, When the same cart is priced, Then both pricings discount 300 after the cap (the
    non-exclusive 400 is capped), so the exclusive one applies: discounts 300 and 0, total 1820;
    without the cap the non-exclusive pricing (400) is larger and applies: discounts 200 and 200,
    total 1720."
    """
    promos = (co.promotions.PercentOff("toys", 3000, exclusive=True), co.promotions.FixedOff(400))
    items = [("TOY", 1), ("JOURNAL", 1)]
    capped = priced(co, items, promos, 300)
    assert line_amounts(capped, "discount") == [300, 0]
    assert capped.total == 1820
    uncapped = priced(co, items, promos)
    assert line_amounts(uncapped, "discount") == [200, 200]
    assert uncapped.total == 1720


# User Story 3 - Returns


def refund_amounts(refund: Any) -> tuple[int, int, int]:
    return (refund.net, refund.tax, refund.total)


def order_of(
    co: Modules,
    items: list[tuple[str, int]],
    promotions: tuple[Any, ...] = (),
    discount_cap: int | None = None,
) -> Any:
    return co.returns.Order(priced(co, items, promotions, discount_cap))


def test_us3_1_full_return_of_a_line(co: Modules) -> None:
    """US3-1: "Given an order with `PEN` ×3 and no promotion (net 597, tax 49), When all 3 units
    are returned, Then the refund's net is 597, its tax 49 and its total 646."
    """
    refund = order_of(co, [("PEN", 3)]).return_units("PEN", 3)
    assert refund_amounts(refund) == (597, 49, 646)


def test_us3_1_zero_priced_return(co: Modules) -> None:
    """US3-1: "Given an order with `STICKER` ×2, When both are returned, Then the refund is 0." """
    refund = order_of(co, [("STICKER", 2)]).return_units("STICKER", 2)
    assert refund_amounts(refund) == (0, 0, 0)


def journal_order(co: Modules) -> Any:
    return order_of(co, [("JOURNAL", 3)], (co.promotions.FixedOff(1000),))


def test_us3_2_partial_return_per_unit_largest_remainder(co: Modules) -> None:
    """US3-2: "Given an order with `JOURNAL` ×3 and 1000 off the order (net 2000, tax 100), When 1
    unit is returned, Then the refund's net is 667 and its tax 34 (the per-unit taxes are 34, 33,
    33), total 701." The net follows from "`JOURNAL` ×3 with net 2000 splits into 667, 667, 666"
    and "the first return of a line takes its first units".
    """
    refund = journal_order(co).return_units("JOURNAL", 1)
    assert refund_amounts(refund) == (667, 34, 701)


def test_us3_3_remaining_units_refund_the_rest(co: Modules) -> None:
    """US3-3: "When the remaining 2 units are returned, Then the refund's net is 1333, its tax 66
    and its total 1399, so the two refunds sum to 2100, exactly what was paid"
    """
    order = journal_order(co)
    first = order.return_units("JOURNAL", 1)
    second = order.return_units("JOURNAL", 2)
    assert refund_amounts(second) == (1333, 66, 1399)
    assert first.total + second.total == 2100


def test_us3_3_one_unit_at_a_time(co: Modules) -> None:
    """US3-3: "returned one unit at a time instead, the refunds are 701, 700 and 699: partial
    returns never refund more than was paid, and a full return refunds all of it."
    """
    order = journal_order(co)
    totals = [order.return_units("JOURNAL", 1).total for _ in range(3)]
    assert totals == [701, 700, 699]


def test_us3_4_full_return_of_a_promoted_order(co: Modules) -> None:
    """US3-4: "Given the order of US2-6 (cap 800; nets 2338 and 862, taxes 117 and 86, total
    3403), When `JOURNAL` ×1, then `TOY` ×1, then `JOURNAL` ×2 are returned, Then the refunds are
    819 (780 + 39), 948 (862 + 86) and 1636 (1558 + 78), which sum to 3403, the order's total."
    """
    order = order_of(co, [("JOURNAL", 3), ("TOY", 1)], cap_promotions(co), 800)
    refunds = [
        order.return_units("JOURNAL", 1),
        order.return_units("TOY", 1),
        order.return_units("JOURNAL", 2),
    ]
    assert [refund_amounts(r) for r in refunds] == [
        (780, 39, 819),
        (862, 86, 948),
        (1558, 78, 1636),
    ]
    assert sum(r.total for r in refunds) == 3403


def test_us3_5_discounts_fixed_at_purchase(co: Modules) -> None:
    """US3-5: "Given an order with `TOY` ×3 and buy 2 get 1 free on `TOY` (net 2000, tax 200),
    When 1 unit is returned, Then the refund is 667 + 67 = 734 (...); when the other 2 are then
    returned, the refund is 1333 + 133 = 1466."
    """
    order = order_of(co, [("TOY", 3)], (co.promotions.BuyXGetY("TOY", 2, 1),))
    assert refund_amounts(order.return_units("TOY", 1)) == (667, 67, 734)
    assert refund_amounts(order.return_units("TOY", 2)) == (1333, 133, 1466)


def test_us3_6_over_return_after_partial(co: Modules) -> None:
    """US3-6: "When 2 units are returned, Then the refund is 431 (398 + 33); when 2 more are asked
    for, Then the return is rejected with `OverReturn`, since only 1 remains, and nothing is
    returned; when 1 is then returned, the refund is 215 (199 + 16); a further return of 1 is
    rejected with `OverReturn`."
    """
    order = order_of(co, [("PEN", 3)])
    assert refund_amounts(order.return_units("PEN", 2)) == (398, 33, 431)
    with pytest.raises(co.returns.OverReturn):
        order.return_units("PEN", 2)
    assert refund_amounts(order.return_units("PEN", 1)) == (199, 16, 215)
    with pytest.raises(co.returns.OverReturn):
        order.return_units("PEN", 1)


def test_us3_6_over_return_on_fresh_order(co: Modules) -> None:
    """US3-6: "Given a fresh order with `PEN` ×3, When 4 units are returned, Then the return is
    rejected with `OverReturn`."
    """
    with pytest.raises(co.returns.OverReturn):
        order_of(co, [("PEN", 3)]).return_units("PEN", 4)


def test_us3_7_rejections_leave_the_order_unchanged(co: Modules) -> None:
    """US3-7: "When a return of 0 or -1 units of `PEN` is asked for, Then it is rejected with
    `InvalidQuantity`; when a return of `TOY`, not in the order, is asked for, Then it is rejected
    with `UnknownSku`; neither changes the order, so returning 3 units of `PEN` afterwards refunds
    646."
    """
    order = order_of(co, [("PEN", 3)])
    for quantity in (0, -1):
        with pytest.raises(co.cart.InvalidQuantity):
            order.return_units("PEN", quantity)
    with pytest.raises(co.catalog.UnknownSku):
        order.return_units("TOY", 1)
    assert order.return_units("PEN", 3).total == 646
