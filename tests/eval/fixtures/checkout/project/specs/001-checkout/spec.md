# Feature Specification: Checkout pricing

**Feature Branch**: `001-checkout`

**Status**: Ready

## Conventions used in every scenario

All money is an integer number of cents: `1050` is $10.50. No amount is ever a fraction of a cent;
every rule below says how a fraction is turned into cents.

The scenarios use this catalog:

| SKU | Unit price (cents) | Category |
|---|---|---|
| `BOOK` | 1050 | `books` |
| `ATLAS` | 1030 | `books` |
| `JOURNAL` | 1000 | `books` |
| `NOTEBOOK` | 1000 | `stationery` |
| `PEN` | 199 | `stationery` |
| `STICKER` | 0 | `stationery` |
| `TOY` | 1000 | `toys` |
| `BREAD` | 350 | `groceries` |
| `LAMP` | 2500 | `garden` |

and this tax table: `books` 5%, `stationery` 8.25%, `toys` 10%, `groceries` 0%. The table has no
rate for `garden`.

Rounding **half-even** means: a fraction of exactly one half rounds to the even cent (82.5 → 82,
157.5 → 158); any other fraction rounds to the nearest cent (16.4175 → 16, 102.45 → 102).

**Largest-remainder allocation** of an amount A over weights w₁…wₙ (W their sum, W > 0) gives item
i the cents ⌊A·wᵢ / W⌋, then hands the cents still unallocated, one each, to the items with the
largest remainders (A·wᵢ mod W), so the shares always sum to exactly A. When two items have equal
remainders, the earlier item gets the cent first. Allocating 0 gives every item 0.

**Inputs this feature does not cover.** Each SKU has at most one buy-X-get-Y promotion in a call;
X and Y are at least 1; a percentage is between 0% and 100%; a fixed amount, a minimum net and a
cap are at least 0; a restocking fee rate is between 0% and 100% and a fee cap is at least 0.
A call that breaks two rules at once (an unknown SKU with quantity 0, say) is rejected with one of
their errors, and which one is not specified. No scenario uses such inputs.

## User Scenarios & Testing

### User Story 1 - Price a cart with tax (Priority: P1)

A shopper fills a cart from the catalog and sees each line's net amount and tax, and the order's
totals.

**Bulk price**: a line of 10 or more units is priced at the bulk unit price, 95% of the catalog unit
price rounded half-even to the cent, and its gross is that unit price × its quantity: the rounding is
done once on the unit price, never on the line's total. The quantity that counts is the line's when
the cart is priced, after every addition to it. Everywhere this spec says a line's unit price, it
means this one: the bulk unit price on a line of 10 or more units, the catalog unit price otherwise.

**Independent Test**: carts built from the catalog above, priced with the tax table above and no
promotions, give the amounts below.

**Acceptance Scenarios**:

1. **US1-1** **Given** an empty cart, **When** SKU `NOPE` (not in the catalog) is added, **Then**
   the addition is rejected with `UnknownSku` and the cart stays empty.
2. **US1-2** **Given** an empty cart, **When** `PEN` is added with quantity 0, 100 or -1, **Then**
   each addition is rejected with `InvalidQuantity` and the cart stays empty; quantities 1 and 99
   are accepted: a line's quantity is a whole number from 1 to 99.
3. **US1-3** **Given** an empty cart, **When** `PEN` ×2, then `BOOK` ×1, then `PEN` ×3 are added,
   **Then** the cart has two lines, `PEN` ×5 then `BOOK` ×1: adding a SKU already in the cart adds
   to that line's quantity and the line keeps its place, and lines are ordered by when their SKU
   was first added. **When** `PEN` ×95 is then added, **Then** it is rejected with
   `InvalidQuantity`, because the line would hold 100, and `PEN` stays at 5.
4. **US1-4** **Given** a cart with `NOTEBOOK` ×1, **When** it is priced, **Then** the line's net is
   1000 (unit price × quantity) and its tax is 82 (8.25% of 1000 is 82.5, rounded half-even);
   **given** `NOTEBOOK` ×3 instead, the net is 3000 and the tax is 248 (247.5 rounded half-even);
   **given** `PEN` ×1, the net is 199 and the tax is 16 (16.4175 rounded). Tax is the line's
   category rate applied to the line's net, rounded half-even to the cent.
5. **US1-5** **Given** a cart with `NOTEBOOK` ×1 and `BOOK` ×1, **When** it is priced, **Then** the
   line taxes are 82 and 52 (52.5 rounded half-even) and the order's tax is 134: tax is rounded per
   line and the order's tax is the sum of the rounded line taxes (rounding the unrounded sum, 135.0,
   is not the rule).
6. **US1-6** **Given** a cart with `BOOK` ×2, `PEN` ×3 and `TOY` ×1, **When** it is priced, **Then**
   the line nets are 2100, 597 and 1000, the line taxes 105, 49 and 100, and the order's net is
   3697, its tax 254 and its total 3951: the order's net is the sum of the line nets, its tax the
   sum of the line taxes, and its total the net plus the tax.
7. **US1-7** **Given** a cart with `STICKER` ×5 and `BREAD` ×4, **When** it is priced, **Then** the
   `STICKER` line's net and tax are 0, the `BREAD` line's net is 1400 and its tax 0 (a 0% category),
   and the order's total is 1400.
8. **US1-8** **Given** a cart with `PEN` ×1 and `LAMP` ×1, **When** it is priced, **Then** pricing
   is rejected with `UnknownCategory`: every line's category must have a rate in the tax table.
9. **US1-9** **Given** an empty cart, **When** `PEN` ×9 then `PEN` ×1 are added and the cart is
   priced, **Then** the line holds 10 units at the bulk unit price 189 (95% of 199 is 189.05,
   rounded half-even): net 1890, tax 156 (155.925 rounded); **given** `PEN` ×9 alone, the unit
   price stays 199: net 1791, tax 148. **Given** `PEN` ×12, **Then** the unit price is 189, the net
   2268 (189 × 12; 95% of the line's 2388 rounded, 2269, is not the rule) and the tax 187 (187.11
   rounded); **given** `ATLAS` ×10, the unit price is 978 (978.5 rounded half-even), the net 9780
   and the tax 489.

### User Story 2 - Promotions (Priority: P2)

The shop runs promotions; the shopper's cart is priced with them, and tax applies to the discounted
amounts.

There are three kinds of promotion, and a cart is priced with any number of them, plus an optional
discount cap:

- **Buy X get Y free** on a SKU: in that SKU's line, of every X + Y units, Y are free. The free
  units are worth the line's unit price each (the bulk unit price on a line of 10 or more units,
  User Story 1).
- **Percentage off** a category: each line of that category gets the percentage of its current net,
  rounded half-even to the cent, as a discount.
- **Fixed amount off** the order: the order's current net is reduced by the amount, but never below
  zero (the discount is the smaller of the amount and the order's current net), and the discount is
  allocated to the lines by largest remainder in proportion to their current nets. A fixed amount
  may carry a **minimum net**: it applies only when the order's current net at the moment it
  applies (after every buy-X-get-Y-free, every percentage off and every fixed amount given before
  it) is at least the minimum; otherwise it takes nothing. Without one, the minimum is 0.

The kinds always apply in this **stacking order**, whatever order the promotions are given in:
first every buy-X-get-Y-free, then every percentage off, then every fixed amount off, then the cap.
Each applies to the nets left by the ones before it ("current net"); promotions of the same kind
apply in the order they are given. A line's discount is the sum of what every promotion took from
it; its net is its gross (unit price × quantity) minus its discount; its tax is computed on that
net as in User Story 1.

The **discount cap**, when given, limits what percentages off and fixed amounts off take; the free
units of buy X get Y free are never capped. When the lines' percentage and fixed-amount discounts
add up to more than the cap, the cap is allocated to the lines by largest remainder in proportion to
each line's percentage and fixed-amount discount before the cap, and each line's discount becomes
its share plus what buy X get Y free took from it.

A promotion may be flagged **exclusive**. The cart is priced once with all the non-exclusive
promotions together, and once with each exclusive promotion alone (each time with the stacking
order and the cap); of these, the pricing with the largest total discount after the cap, free units
included, is the one the shopper gets. When an exclusive pricing and the non-exclusive pricing give equal total
discounts, the exclusive one applies; when two exclusive pricings tie, the one whose promotion was
given first applies. With no non-exclusive promotion, the non-exclusive pricing has a total
discount of 0.

**Independent Test**: carts built from the catalog above, priced with the tax table above and the
promotions below, give the amounts below.

**Acceptance Scenarios**:

1. **US2-1** **Given** buy 2 get 1 free on `TOY`, **When** a cart with `TOY` ×5 is priced, **Then**
   the line's discount is 1000 (one free unit: of every 3 units, 1 is free, and 5 units hold one
   group of 3), its net 4000 and its tax 400; with `TOY` ×6 the discount is 2000; with `TOY` ×2 it
   is 0. **Given** buy 1 get 1 free on `STICKER`, **When** a cart with `STICKER` ×4 is priced,
   **Then** two units are free and the discount is 0, since a free unit at zero price is worth 0.
2. **US2-2** **Given** 15% off `books`, **When** a cart with `BOOK` ×1, `ATLAS` ×1 and `TOY` ×1 is
   priced, **Then** the `BOOK` discount is 158 (157.5 rounded half-even) with net 892 and tax 45,
   the `ATLAS` discount is 154 (154.5 rounded half-even) with net 876 and tax 44, and `TOY`, not a
   book, has discount 0 and tax 100. **Given** 10% off `toys` and then 20% off `toys`, **When** a
   cart with `TOY` ×1 is priced, **Then** the discount is 280 and the net 720: the second
   percentage applies to the 900 the first left.
3. **US2-3** **Given** buy 2 get 1 free on `TOY`, 10% off `toys` and 500 off the order, **When** a
   cart with `TOY` ×3 is priced, **Then** the free unit takes 1000 (net 2000), the percentage 200
   (net 1800) and the fixed amount 500, so the discount is 1700, the net 1300, the tax 130 and the
   total 1430; the same three promotions given in the reverse order price the same, since the
   stacking order does not depend on the order they are given in.
4. **US2-4** **Given** 100 off the order, **When** a cart with `TOY` ×1, `STICKER` ×3, `BOOK` ×2
   and `PEN` ×5 (current nets 1000, 0, 2100 and 995) is priced, **Then** the line discounts are 25,
   0, 51 and 24 (the floors 24, 0, 51 and 24 leave one cent, which goes to `TOY`, the largest
   remainder), the line nets 975, 0, 2049 and 971, the line taxes 98, 0, 102 and 80, and the
   order's total 4275: tax is computed on the discounted line nets, and a zero-priced line gets no
   share. **Given** 5000 off the order, **When** a cart with `TOY` ×1 and `BOOK` ×1 is priced,
   **Then** the discount is 2050 (1000 and 1050), every net and tax is 0 and the total is 0: a
   fixed amount never takes the order below zero.
5. **US2-5** **Given** 1 off the order, **When** a cart with `TOY` ×1 and `JOURNAL` ×1 (equal nets)
   is priced, **Then** `TOY`, the earlier line, gets the cent: discounts 1 and 0. **Given** 100 off
   the order, **When** a cart with `NOTEBOOK` ×1, `TOY` ×1 and `JOURNAL` ×1 is priced, **Then** the
   discounts are 34, 33 and 33: equal remainders, so the leftover cent goes to the earliest line.
6. **US2-6** **Given** 20% off `books`, 10% off `toys`, 200 off the order and a discount cap of
   800, **When** a cart with `JOURNAL` ×3 and `TOY` ×1 is priced, **Then** the discounts before the
   cap are 745 and 155 (percentages 600 and 100; the 200 off allocated 145 and 55 over current nets
   2400 and 900), 900 in all, more than the cap; the cap of
   800 is allocated over 745 and 155, giving discounts 662 and 138, nets 2338 and 862, taxes 117
   and 86, and an order net of 3200, tax 203 and total 3403. With a cap of 1000 instead, the cap is
   not reached: discounts 745 and 155, nets 2255 and 845, taxes 113 (112.75 rounded) and 84 (84.5
   rounded half-even), total 3297.
7. **US2-7** **Given** an exclusive 30% off `toys` and the non-exclusive 10% off `toys` and 100
   off the order, **When** a cart with `TOY` ×2 is priced, **Then** the exclusive pricing (discount
   600) beats the non-exclusive one (200 + 100 = 300): discount 600, net 1400, tax 140, total 1540.
   With an exclusive 5% off `toys` (discount 100) instead, the non-exclusive pricing applies:
   discount 300, net 1700, tax 170. With both exclusives, the 30% (600) is the best exclusive and
   applies. **Given** an exclusive 600 off the order given first and an exclusive 30% off `toys`
   given second, **When** a cart with `TOY` ×2 and `JOURNAL` ×1 is priced, **Then** both take 600,
   so the one given first applies: discounts 400 and 200; given in the other order, the 30% applies:
   discounts 600 and 0.
8. **US2-8** **Given** an exclusive 10% off `toys` and a non-exclusive 100 off the order, **When**
   a cart with `TOY` ×1 and `JOURNAL` ×1 is priced, **Then** both pricings discount 100, so the
   exclusive one applies: discounts 100 and 0, taxes 90 and 50, total 2040. **Given** an exclusive
   30% off `toys`, a non-exclusive 400 off the order and a discount cap of 300, **When** the same
   cart is priced, **Then** both pricings discount 300 after the cap (the non-exclusive 400 is
   capped), so the exclusive one applies: discounts 300 and 0, total 1820; without the cap the
   non-exclusive pricing (400) is larger and applies: discounts 200 and 200, total 1720.
9. **US2-9** **Given** buy 2 get 1 free on `TOY`, **When** a cart with `TOY` ×12 is priced,
   **Then** 4 units are free, each worth the line's bulk unit price 950: discount 3800, net 7600,
   tax 760.
10. **US2-10** **Given** 10% off `toys` and 300 off the order with a minimum net of 2000, **When**
   a cart with `TOY` ×2 is priced, **Then** the order's current net when the fixed amount applies
   is 1800 (after the percentage), below the minimum, so it takes nothing: discount 200, net 1800;
   with a minimum net of 1800 instead, it applies: discount 500, net 1500. **Given** 100 off the
   order with a minimum net of 1600 given first and 500 off the order given second, **When** a cart
   with `TOY` ×2 is priced, **Then** the 100 applies at 2000 and the 500 after it: discount 600,
   net 1400; given in the other order, the 500 leaves 1500, below 1600, and the 100 takes nothing:
   discount 500, net 1500.
11. **US2-11** **Given** an exclusive 300 off the order with a minimum net of 2000 and a
   non-exclusive 10% off `toys`, **When** a cart with `TOY` ×2 is priced, **Then** the exclusive
   pricing, priced alone, meets its minimum at 2000 and discounts 300, more than the non-exclusive
   200: discount 300, net 1700, tax 170.
12. **US2-12** **Given** buy 2 get 1 free on `TOY`, 300 off the order and a discount cap of 200,
   **When** a cart with `TOY` ×3 and `JOURNAL` ×1 is priced, **Then** the free unit takes 1000 from
   `TOY` and is not capped; the 300 off (200 and 100, allocated over current nets 2000 and 1000) is
   more than the cap, so the cap of 200 is allocated over 200 and 100, giving 133 and 67; the line
   discounts are 1133 and 67, the nets 1867 and 933, the taxes 187 (186.7 rounded) and 47 (46.65
   rounded), and the order's discount is 1200, its net 2800, its tax 234 and its total 3034. With a
   cap of 300 instead, the 300 off is not more than the cap: discounts 1200 and 100.
13. **US2-13** **Given** the promotions and the cap of 200 of US2-12 and also an exclusive 1100 off
   the order, **When** the same cart is priced, **Then** the exclusive pricing discounts 200 after
   the cap and the non-exclusive pricing 1200, free units included, so the non-exclusive pricing
   applies: discounts 1133 and 67.

### User Story 3 - Returns (Priority: P3)

A shopper returns units of a priced order and gets back exactly what those units cost, promotions
and tax included.

A return names a SKU of the order and a number of units. Each line's net and tax are split into
per-unit amounts by largest remainder over equal weights, one per unit, so the earlier units get
the leftover cents (`JOURNAL` ×3 with net 2000 splits into 667, 667, 666). The amounts are those of
the order as priced: a return never re-evaluates a promotion. Returns take a line's units in order:
the first return of a line takes its first units, the next return the units after them. A refund's
net is the sum of its units' net amounts, its tax the sum of their tax amounts, and its total the
net plus the tax minus its fee.

An order may carry a **restocking fee**: a rate, and optionally a fee cap. A return's fee is the
rate applied to the refund's net (not its tax), rounded half-even to the cent once for the return,
not per unit. The fee cap limits the fees of all the order's returns together: a return's fee is the
smaller of that amount and what the cap has left after the order's earlier returns. A rejected
return charges no fee. Without a restocking fee, every fee is 0.

**Independent Test**: orders priced as in User Stories 1 and 2, then returned in part or in full,
give the refunds below.

**Acceptance Scenarios**:

1. **US3-1** **Given** an order with `PEN` ×3 and no promotion (net 597, tax 49), **When** all 3
   units are returned, **Then** the refund's net is 597, its tax 49 and its total 646. **Given** an
   order with `STICKER` ×2, **When** both are returned, **Then** the refund is 0.
2. **US3-2** **Given** an order with `JOURNAL` ×3 and 1000 off the order (net 2000, tax 100),
   **When** 1 unit is returned, **Then** the refund's net is 667 and its tax 34 (the per-unit taxes
   are 34, 33, 33), total 701.
3. **US3-3** **Given** the order of US3-2 after that return, **When** the remaining 2 units are
   returned, **Then** the refund's net is 1333, its tax 66 and its total 1399, so the two refunds
   sum to 2100, exactly what was paid; returned one unit at a time instead, the refunds are 701,
   700 and 699: partial returns never refund more than was paid, and a full return refunds all of
   it.
4. **US3-4** **Given** the order of US2-6 (cap 800; nets 2338 and 862, taxes 117 and 86, total
   3403), **When** `JOURNAL` ×1, then `TOY` ×1, then `JOURNAL` ×2 are returned, **Then** the
   refunds are 819 (780 + 39), 948 (862 + 86) and 1636 (1558 + 78), which sum to 3403, the order's
   total.
5. **US3-5** **Given** an order with `TOY` ×3 and buy 2 get 1 free on `TOY` (net 2000, tax 200),
   **When** 1 unit is returned, **Then** the refund is 667 + 67 = 734, its share of what was paid,
   not the unit price and not 0, though the 2 units left no longer make a group of 3; **when** the
   other 2 are then returned, the refund is 1333 + 133 = 1466.
6. **US3-6** **Given** an order with `PEN` ×3 (per-unit nets 199, 199, 199; per-unit taxes 17, 16,
   16), **When** 2 units are returned, **Then** the refund is 431 (398 + 33); **when** 2 more are
   asked for, **Then** the return is rejected with `OverReturn`, since only 1 remains, and nothing
   is returned; **when** 1 is then returned, the refund is 215 (199 + 16); a further return of 1 is
   rejected with `OverReturn`. **Given** a fresh order with `PEN` ×3, **When** 4 units are
   returned, **Then** the return is rejected with `OverReturn`.
7. **US3-7** **Given** an order with `PEN` ×3, **When** a return of 0 or -1 units of `PEN` is
   asked for, **Then** it is rejected with `InvalidQuantity`; **when** a return of `TOY`, not in the
   order, is asked for, **Then** it is rejected with `UnknownSku`; neither changes the order, so
   returning 3 units of `PEN` afterwards refunds 646.
8. **US3-8** **Given** the order of US3-2 (per-unit nets 667, 667, 666; per-unit taxes 34, 33, 33)
   with a restocking fee of 2.5% and no fee cap, **When** 2 units are returned, **Then** the
   refund's net is 1334, its tax 67, its fee 33 (2.5% of 1334 is 33.35; per unit it would be 17 +
   17 = 34) and its total 1368; **when** the last unit is then returned, its fee is 17 (16.65
   rounded) and its total 682 (666 + 33 − 17).
9. **US3-9** **Given** the order of US3-2 with a restocking fee of 2.5% and a fee cap of 30,
   **When** 1 unit is returned, **Then** its fee is 17 (16.675 rounded) and its total 684 (667 +
   34 − 17); **when** 3 more are asked for, **Then** the return is rejected with `OverReturn` and
   charges no fee; **when** the remaining 2 are returned, **Then** their fee before the cap is 33
   (33.325 rounded), but the cap has 13 left, so the fee is 13 and the total 1386 (1333 + 66 − 13).

## Requirements

- **FR-001**: Money is integer cents; tax and percentage discounts round half-even per line;
  allocations use largest remainder with the earlier item first on equal remainders (Conventions).
- **FR-002**: A cart holds at most one line per SKU, each of quantity 1 to 99, in the order the SKUs
  were first added; an unknown SKU or a quantity outside 1–99 is rejected (User Story 1).
- **FR-003**: A priced order gives each line's unit price (the bulk price at 10 or more units),
  gross, discount, net and tax, and the order's gross, discount, net, tax and total (User Stories 1
  and 2).
- **FR-004**: Promotions follow the stacking order, the minimum net, the cap (free units never
  capped) and exclusivity of User Story 2.
- **FR-005**: Returns refund per-unit amounts fixed at purchase, in unit order, and reject a return
  of more units than remain, of fewer than 1, or of a SKU not in the order, less a restocking fee
  rounded once per return and capped across the order's returns (User Story 3).
