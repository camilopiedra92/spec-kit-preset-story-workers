# Tasks: Checkout pricing

**Input**: `specs/001-checkout/` (spec.md, plan.md)

**Tests**: requested; each story's tests are written first and seen failing.

## Phase 1: Setup

- [ ] T001 Create `src/checkout/__init__.py` with a package docstring, and `tests/` with a `conftest.py` that is empty but for a docstring; `uv run pytest` and `uv run ruff check` run

## Phase 2: User Story 1 - Price a cart with tax (Priority: P1)

- [ ] T002 [US1] Write `tests/test_catalog.py`: the acceptance scenario US1-1 (an unknown SKU)
- [ ] T003 [US1] Write `tests/test_cart.py`: the acceptance scenarios US1-2 and US1-3 (quantities, and adding a SKU already in the cart)
- [ ] T004 [US1] Write `tests/test_tax.py`: the acceptance scenarios US1-4, US1-5, US1-7 and US1-8 (per-line half-even tax, a zero price, a 0% category, a category without a rate)
- [ ] T005 [US1] Write `tests/test_pricing.py`: the acceptance scenario US1-6 (the order's net, tax and total); run the tests of T002–T005 and see them fail
- [ ] T006 [US1] Implement `apply_rate` in `src/checkout/money.py`
- [ ] T007 [US1] Implement `UnknownSku`, `Product` and `Catalog` in `src/checkout/catalog.py`
- [ ] T008 [US1] Implement `UnknownCategory`, `TaxTable` and `line_tax` in `src/checkout/tax.py`
- [ ] T009 [US1] Implement `InvalidQuantity`, `CartLine` and `Cart` in `src/checkout/cart.py`
- [ ] T010 [US1] Implement `PricedLine`, `Receipt` and `price` without promotions in `src/checkout/cart.py`; `uv run pytest` and `uv run ruff check` pass

## Phase 3: User Story 2 - Promotions (Priority: P2)

- [ ] T011 [US2] Write `tests/test_promotions.py`: the acceptance scenarios US2-1, US2-2 and US2-3 (buy X get Y, percentage off, the stacking order)
- [ ] T012 [US2] Write `tests/test_allocation.py`: the acceptance scenarios US2-4 and US2-5 (a fixed amount allocated by largest remainder, never below zero, and its tie-break)
- [ ] T013 [US2] Write `tests/test_exclusivity.py`: the acceptance scenarios US2-6, US2-7 and US2-8 (the cap, exclusivity and its tie-breaks); run the tests of T011–T013 and see them fail
- [ ] T014 [US2] Implement `allocate` in `src/checkout/allocation.py`
- [ ] T015 [US2] Implement `BuyXGetY`, `PercentOff`, `FixedOff`, `Promotion` and the stacking order in `line_discounts` in `src/checkout/promotions.py`
- [ ] T016 [US2] Add the discount cap to `line_discounts` in `src/checkout/promotions.py`, allocating the cap with `allocate` from `src/checkout/allocation.py`
- [ ] T017 [US2] Add exclusivity and its tie-breaks to `line_discounts` in `src/checkout/promotions.py`
- [ ] T018 [US2] Price with promotions in `price` in `src/checkout/cart.py`: the `promotions` and `discount_cap` parameters, each line's discount from `line_discounts`, tax on the discounted net; `uv run pytest` and `uv run ruff check` pass

## Phase 4: User Story 3 - Returns (Priority: P3)

- [ ] T019 [US3] Write `tests/test_returns.py`: the acceptance scenarios US3-1 to US3-5 (full and partial refunds, refunds summing to what was paid, discounts fixed at purchase)
- [ ] T020 [US3] Write `tests/test_return_rejections.py`: the acceptance scenarios US3-6 and US3-7 (over-returns, quantities below 1, a SKU not in the order); run the tests of T019–T020 and see them fail
- [ ] T021 [US3] Implement `per_unit` in `src/checkout/allocation.py`
- [ ] T022 [US3] Add `unit_nets` and `unit_taxes` to `PricedLine` in `src/checkout/cart.py`, filled by `price` with `per_unit`
- [ ] T023 [US3] Implement `Refund`, `Order` and `Order.return_units` in `src/checkout/returns.py`: units taken in order, the refund summing their per-unit amounts
- [ ] T024 [US3] Implement `OverReturn` and the rejections of `Order.return_units` in `src/checkout/returns.py` (more units than remain, fewer than 1, a SKU not in the order), leaving the order unchanged; `uv run pytest` and `uv run ruff check` pass

## Dependencies

Phase 1 → Phase 2 → Phase 3 → Phase 4.
