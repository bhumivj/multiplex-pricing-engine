# Reasoning & Design Decisions

## Problem Interpretation
The task is a pricing engine, not a booking system: given a tier, quantity,
and membership status, produce a correct, itemized bill and reject invalid or
oversold requests. No UI, storage, or API was requested or built.

## Architecture
Single module `pricing/engine.py`. Two pure functions:
- `price_single_ticket` — price for one ticket (used to prove correctness in isolation)
- `price_booking` — validates availability, then multiplies by quantity

Business rule values are isolated into one `PricingConfig` dataclass, so
correction of a number never requires touching calculation logic. Types
(`Tier`, `TicketBreakdown`, `BillBreakdown`, `PricingError`) make the
input/output contract explicit and prevent silent errors.

## Pricing Calculation Flow
1. Look up base tier price
2. Subtract flat festival discount
3. Subtract percentage member discount (on the post-festival amount), capped
4. Add convenience fee
5. Apply GST on (discounted price + fee)
6. Round at every step, never only at the end

## Tier & Availability Handling
Each `Tier` carries an `available_seats` integer. A booking is rejected if:
- the tier doesn't exist
- `available_seats == 0` (sold out)
- `available_seats < requested quantity` (insufficient stock)

This was chosen over a boolean "sold out" flag because the problem
statement mentions tiers "selling out," implying a countable stock, and an
integer model supports both checks without extra state.

## Festival Discount
Flat ₹50 per ticket, applied first, before member discount. Chosen as the
first deduction because "flat festival discount" reads as a base-price
markdown, distinct from member status. If the discount would exceed the
base price, it's capped to the base price so a ticket never goes negative.

## Member Discount & Cap
10% of the *post-festival* price, capped at ₹100/ticket. Calculated after
festival discount, per the confirmed order — stacking on the already
reduced price (not the original price) prevents double-dipping on the same
rupee.

## Discount Order
Festival → Member. Confirmed explicitly before implementation since the
order changes the final number and was not specified in the original
prompt.

## Convenience Fee
Added after both discounts, before tax — treated as a service charge on the
discounted transaction, not part of the discountable ticket price.

## GST
18% applied on (discounted ticket price + convenience fee) — i.e. GST taxes
the full amount the customer is billed for that ticket, matching how
convenience fees are commonly taxed in Indian ticketing platforms.

## Exact Monetary Arithmetic
All values are `decimal.Decimal`, constructed from strings (`"150.00"`), not
`float`. `float` was avoided entirely because binary floating point cannot
represent most decimal fractions exactly, which would break the "exact
paisa" requirement over successive operations.

## Rounding Strategy
`ROUND_HALF_UP` at 2 decimal places, applied after every individual
calculation (festival discount, member discount, GST, final price) — not
just once at the end. This guarantees the sum of displayed line items always
equals the displayed total; rounding only at the end can make bill line
items and totals visually inconsistent.

## Validation / Error Handling
A single `PricingError(ValueError)` type is raised for all business-rule
violations: unknown tier, sold out, insufficient seats, invalid quantity
(zero, negative, non-integer, or boolean). Booleans are explicitly excluded
because Python treats `bool` as a subtype of `int`, which would otherwise
let `True`/`False` silently pass as quantities 1/0.

## Bill Breakdown
`TicketBreakdown` exposes every intermediate value (base price → festival
discount → member discount → fee → taxable amount → GST → final price) so
the counter can print a full line-by-line receipt, not just a total.
`BillBreakdown` aggregates this across quantity.

## Testing Strategy
29 `pytest` tests, one behavior per test, organized by the 17 required
categories: base tier pricing, mixed-tier bookings, each discount in
isolation, discount ordering, fee, GST, exact paisa values, rounding
behavior, all four invalid-input types, sold-out and insufficient-seat
cases, member vs non-member totals, full end-to-end billing, and boundary
cases (exact remaining seats, single ticket, large quantity).

## Important Edge Cases Covered
- Festival discount larger than base price (clamped to zero, not negative)
- Member discount exceeding the cap
- Booking exactly the remaining seat count
- Non-integer and boolean quantities
- Large quantity bookings (100 tickets)

## Assumptions (values not specified in the original problem statement)
Tier prices, festival discount amount, member discount percentage and cap,
discount order, convenience fee amount, GST rate and taxable base, and the
rounding rule were all unspecified. Defaults were proposed, confirmed
explicitly, and stored as one configurable block rather than hard-coded
into logic — see the "Business Rules" table in README.md.

## Limitations
- No persistence layer; seat availability must be supplied by the caller
- No API or CLI; this is a pricing library, matching the scope of the task
- Multi-tier bookings in a single cart are handled by calling
  `price_booking` once per tier and summing results, not by a single
  combined-cart function