# Tasks: Checkout pricing

**Input**: `specs/001-checkout/` (spec.md, plan.md)

**Tests**: requested; each story's tests are written first and seen failing.

## Phase 1: Setup

- [X] T001 Create `src/checkout/__init__.py` with a package docstring, and `tests/` with a `conftest.py` that is empty but for a docstring; `uv run pytest` and `uv run ruff check` run

## Phase 2: User Story 1 - Price a cart with tax (Priority: P1)

- [X] T002 [US1] Write `tests/test_catalog.py`: the acceptance scenario US1-1 (an unknown SKU)
- [X] T003 [US1] Write `tests/test_cart.py`: the acceptance scenarios US1-2 and US1-3 (quantities, and adding a SKU already in the cart)
- [X] T004 [US1] Write `tests/test_tax.py`: the acceptance scenarios US1-4, US1-5, US1-7 and US1-8 (per-line half-even tax, a zero price, a 0% category, a category without a rate)
- [X] T005 [US1] Write `tests/test_pricing.py`: the acceptance scenarios US1-6 and US1-9 (the order's net, tax and total; the bulk price); run the tests of T002–T005 and see them fail
- [X] T006 [US1] Implement `apply_rate` in `src/checkout/money.py`
- [X] T007 [US1] Implement `UnknownSku`, `Product` and `Catalog` in `src/checkout/catalog.py`
- [X] T008 [US1] Implement `line_unit_price` in `src/checkout/catalog.py`, the bulk unit price with `apply_rate` from `src/checkout/money.py`
- [X] T009 [US1] Implement `UnknownCategory`, `TaxTable` and `line_tax` in `src/checkout/tax.py`
- [X] T010 [US1] Implement `InvalidQuantity`, `CartLine` and `Cart` in `src/checkout/cart.py`
- [X] T011 [US1] Implement `PricedLine`, `Receipt` and `price` without promotions in `src/checkout/cart.py`, each line at `line_unit_price`; `uv run pytest` and `uv run ruff check` pass

## Phase 3: User Story 2 - Promotions (Priority: P2)

- [X] T012 [US2] Write `tests/test_promotions.py`: the acceptance scenarios US2-1, US2-2, US2-3 and US2-9 (buy X get Y, percentage off, the stacking order, free units at the bulk unit price)
- [X] T013 [US2] Write `tests/test_allocation.py`: the acceptance scenarios US2-4, US2-5 and US2-10 (a fixed amount allocated by largest remainder, never below zero, its tie-break, and its minimum net)
- [X] T014 [US2] Write `tests/test_exclusivity.py`: the acceptance scenarios US2-6, US2-7, US2-8, US2-11, US2-12 and US2-13 (the cap, free units outside it, exclusivity and its tie-breaks); run the tests of T012–T014 and see them fail
- [X] T015 [US2] Implement `allocate` in `src/checkout/allocation.py`
- [X] T016 [US2] Implement `BuyXGetY`, `PercentOff`, `FixedOff`, `Promotion` and the stacking order in `line_discounts` in `src/checkout/promotions.py`, free units worth `line_unit_price` from `src/checkout/catalog.py`
- [X] T017 [US2] Add the minimum net (`FixedOff.min_net`) to `line_discounts` in `src/checkout/promotions.py`
- [X] T018 [US2] Add the discount cap to `line_discounts` in `src/checkout/promotions.py`, allocating the cap with `allocate` from `src/checkout/allocation.py`
- [X] T019 [US2] Keep the free units of buy X get Y free outside the discount cap in `line_discounts` in `src/checkout/promotions.py`
- [X] T020 [US2] Add exclusivity and its tie-breaks to `line_discounts` in `src/checkout/promotions.py`
- [X] T021 [US2] Price with promotions in `price` in `src/checkout/cart.py`: the `promotions` and `discount_cap` parameters, each line's discount from `line_discounts`, tax on the discounted net; `uv run pytest` and `uv run ruff check` pass

## Phase 4: User Story 3 - Returns (Priority: P3)

- [X] T022 [US3] Write `tests/test_returns.py`: the acceptance scenarios US3-1 to US3-5 (full and partial refunds, refunds summing to what was paid, discounts fixed at purchase)
- [X] T023 [US3] Write `tests/test_return_rejections.py`: the acceptance scenarios US3-6 and US3-7 (over-returns, quantities below 1, a SKU not in the order)
- [X] T024 [US3] Write `tests/test_return_fees.py`: the acceptance scenarios US3-8 and US3-9 (the restocking fee, rounded once per return, and its cap across returns); run the tests of T022–T024 and see them fail
- [X] T025 [US3] Implement `per_unit` in `src/checkout/allocation.py`
- [X] T026 [US3] Add `unit_nets` and `unit_taxes` to `PricedLine` in `src/checkout/cart.py`, filled by `price` with `per_unit`
- [X] T027 [US3] Implement `Refund`, `Order` and `Order.return_units` in `src/checkout/returns.py`: units taken in order, the refund summing their per-unit amounts
- [X] T028 [US3] Implement `OverReturn` and the rejections of `Order.return_units` in `src/checkout/returns.py` (more units than remain, fewer than 1, a SKU not in the order), leaving the order unchanged
- [X] T029 [US3] Add the restocking fee to `src/checkout/returns.py`: `Refund.fee`, `Order`'s `fee_basis_points`, the fee with `apply_rate` from `src/checkout/money.py`
- [X] T030 [US3] Add the fee cap across the order's returns (`Order`'s `fee_cap`) in `src/checkout/returns.py`; `uv run pytest` and `uv run ruff check` pass
- [X] T031 [US3] Add a section `## Returns as built` to `specs/001-checkout/plan.md`: the order in which `Order.return_units` takes a line's units, and where the restocking fee is rounded

## Dependencies

Phase 1 → Phase 2 → Phase 3 → Phase 4.
