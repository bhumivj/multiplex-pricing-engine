
# Multiplex Pricing Engine

## Overview
A pricing engine for a multiplex ticket counter. Computes exact, line-by-line
ticket bills across seat tiers, discounts, fees, and tax — with no floating-point
rounding errors and no invalid/oversold bookings.

## Features
- Three seat tiers: Silver, Gold, Recliner
- Per-tier seat availability with sold-out enforcement
- Flat festival discount (per ticket)
- Percentage member discount with a hard cap
- Convenience fee per ticket
- GST calculation
- Exact paisa-level arithmetic (Python `Decimal`, never `float`)
- Round-half-up rounding at every line item
- Full line-by-line bill breakdown
- Clean, typed error handling for invalid input

## Business Rules (Configured Defaults)
These values are **not specified** in the original problem statement. They were
agreed as defaults and are configurable in one place: `PricingConfig` in
`pricing/engine.py`.

| Rule | Value |
|---|---|
| Silver price | ₹150.00 |
| Gold price | ₹250.00 |
| Recliner price | ₹400.00 |
| Festival discount | ₹50.00 per ticket, applied first |
| Member discount | 10% of post-festival price, capped at ₹100.00/ticket |
| Convenience fee | ₹20.00 per ticket, added after discounts |
| GST | 18% on (discounted price + convenience fee) |
| Rounding | Round-half-up to nearest paisa, applied at each step |
| Availability | Integer `available_seats` per tier; tier bookable only if > 0 |

## Technology
- Python 3.10+
- `pytest` for testing
- No frameworks, no database, no API, no frontend — logic only

## Project Structure