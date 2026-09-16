
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

## Messy Price List Import
A separate importer (`pricing/importer.py`) cleans a raw, messy seat-class
price list before it's used by the pricing engine.

### Supported Price Formats
- `150`
- `150.00`
- `₹150`
- `₹150.00`
(Commas are also stripped, e.g. `₹1,500.00`.)

### Case-Insensitive Tier Normalization
Tier names are normalized with `.strip().title()`, so `"gold"`, `"GOLD"`,
and `"Gold"` are all treated as the same tier (`"Gold"`).

### Rejection Rules
A record is rejected, with a reason, if:
- the tier name is blank
- the price is blank/missing
- the price is negative
- the price is not a parseable number/currency format

### Duplicate Handling
When the same tier name (case-insensitive) appears more than once:
- **Same price** → later entries are logged as duplicates and ignored.
- **Conflicting price** → later entries are logged as duplicates and
  rejected; the **first valid price seen is kept** (see REASONING.md for
  why this default was chosen).

### Import Report
Every import produces an `ImportReport` with:
- `imported` — records successfully cleaned and kept
- `duplicates` — records ignored/rejected for being duplicates, with reason
- `rejected` — records rejected for bad data, with reason
- `cleaned_prices` — final `{tier_name: Decimal(price)}` dict

### Running the Importer
```bash
python3 -c "
from pricing.importer import import_price_list

messy_data = [
    {'name': 'Silver', 'price': '150'},
    {'name': 'SILVER', 'price': '150.00'},
    {'name': 'gold', 'price': '₹250'},
    {'name': 'Gold', 'price': '300'},
    {'name': 'Recliner', 'price': ''},
    {'name': 'VIP', 'price': '-50'},
    {'name': 'Balcony', 'price': 'abc'},
]

report = import_price_list(messy_data)
print('Cleaned:', report.cleaned_prices)
print('Imported:', report.imported)
print('Duplicates:', report.duplicates)
print('Rejected:', report.rejected)
"
```

### Example Output

## Technology
- Python 3.10+
- `pytest` for testing
- No frameworks, no database, no API, no frontend — logic only

## Project Structure