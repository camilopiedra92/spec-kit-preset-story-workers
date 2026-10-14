# Implementation Plan: Checkout pricing

**Branch**: `001-checkout` | **Spec**: [spec.md](spec.md)

## Summary

A package of seven modules: money arithmetic and allocation at the bottom, the catalog and tax
table beside them, promotions on top of those, the cart and its pricing on top of promotions, and
returns on top of a priced order. Every amount is an `int` of cents.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: none at runtime; pytest and ruff for development, through uv.

**Testing**: `uv run pytest` (the suite) and `uv run ruff check` (the static check).

**Project Type**: a library package.

## Interface

Rates and percentages are integers of basis points: 825 is 8.25%, 1500 is 15%. Every dataclass is
`@dataclass(frozen=True)`. Imports flow one way: `money`, `allocation` ← `catalog`, `tax` ←
`promotions` ← `cart` ← `returns`.

### `src/checkout/money.py`

- `apply_rate(amount: int, basis_points: int) -> int`: `amount × basis_points / 10000`, rounded
  half-even to the cent (spec, Conventions). Used for tax and for percentage discounts.

### `src/checkout/allocation.py`

- `allocate(amount: int, weights: Sequence[int]) -> list[int]`: largest-remainder allocation (spec,
  Conventions); one share per weight, in order, summing to `amount`. When `amount` is 0 every share
  is 0, whatever the weights.
- `per_unit(amount: int, quantity: int) -> list[int]`: `allocate(amount, [1] * quantity)`, the
  per-unit split of User Story 3.

### `src/checkout/catalog.py`

- `class UnknownSku(Exception)`: a SKU not in the catalog (User Story 1) or not in the order
  (User Story 3).
- `Product(sku: str, unit_price: int, category: str)`: a dataclass.
- `Catalog(products: Iterable[Product])`: `Catalog.get(sku: str) -> Product`, raising `UnknownSku`.

### `src/checkout/tax.py`

- `class UnknownCategory(Exception)`: a category with no rate in the table.
- `TaxTable(rates: Mapping[str, int])`: category to basis points; `TaxTable.rate(category: str) ->
  int`, raising `UnknownCategory`.
- `line_tax(net: int, basis_points: int) -> int`: `apply_rate(net, basis_points)`.

### `src/checkout/promotions.py`

- `BuyXGetY(sku: str, buy: int, get: int, exclusive: bool = False)`: buy X get Y free on a SKU.
- `PercentOff(category: str, basis_points: int, exclusive: bool = False)`: percentage off a
  category.
- `FixedOff(amount: int, exclusive: bool = False)`: a fixed amount off the order.
- `Promotion = BuyXGetY | PercentOff | FixedOff`: a type alias.
- `line_discounts(items: Sequence[tuple[Product, int]], promotions: Sequence[Promotion],
  discount_cap: int | None = None) -> list[int]`: each item is a line's product and quantity, in
  cart order; returns each line's discount after the stacking order, the cap and exclusivity of
  User Story 2.

### `src/checkout/cart.py`

- `class InvalidQuantity(ValueError)`: a quantity outside 1–99 (User Story 1), or a return of
  fewer than 1 unit (User Story 3).
- `CartLine(product: Product, quantity: int)`: a dataclass.
- `Cart(catalog: Catalog)`: `Cart.add(sku: str, quantity: int) -> None`, raising `UnknownSku` or
  `InvalidQuantity` and leaving the cart unchanged when it does; `Cart.lines -> tuple[CartLine,
  ...]`, a property, in the order SKUs were first added.
- `PricedLine(sku: str, quantity: int, unit_price: int, gross: int, discount: int, net: int, tax:
  int, unit_nets: tuple[int, ...], unit_taxes: tuple[int, ...])`: a dataclass; `gross` is unit
  price × quantity, `net` is `gross - discount`; `unit_nets` and `unit_taxes` are `per_unit(net,
  quantity)` and `per_unit(tax, quantity)` (User Story 3).
- `Receipt(lines: tuple[PricedLine, ...], gross: int, discount: int, net: int, tax: int, total:
  int)`: a dataclass; the order amounts are the sums of the line amounts, `total = net + tax`.
- `price(cart: Cart, taxes: TaxTable, promotions: Sequence[Promotion] = (), discount_cap: int |
  None = None) -> Receipt`: raising `UnknownCategory`.

### `src/checkout/returns.py`

- `class OverReturn(ValueError)`: more units than remain in the line.
- `Refund(sku: str, quantity: int, net: int, tax: int, total: int)`: a dataclass.
- `Order(receipt: Receipt)`: `Order.return_units(sku: str, quantity: int) -> Refund`, raising
  `UnknownSku`, `InvalidQuantity` or `OverReturn` and leaving the order unchanged when it does.

Tests live in `tests/`, one file per area, named in `tasks.md`.

## Project Structure

```text
src/checkout/__init__.py
src/checkout/money.py
src/checkout/allocation.py
src/checkout/catalog.py
src/checkout/tax.py
src/checkout/promotions.py
src/checkout/cart.py
src/checkout/returns.py
tests/conftest.py
tests/test_*.py
```
