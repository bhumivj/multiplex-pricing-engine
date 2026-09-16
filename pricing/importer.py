"""Importer for messy seat-class price lists.

Kept separate from pricing/engine.py — this module only cleans and
reports on raw input. It does not do any pricing math.
"""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional


@dataclass
class ImportedRecord:
    original_name: str
    normalized_name: str
    raw_price: str
    price: Decimal


@dataclass
class DuplicateRecord:
    original_name: str
    normalized_name: str
    raw_price: str
    reason: str


@dataclass
class RejectedRecord:
    original_name: str
    raw_price: str
    reason: str


@dataclass
class ImportReport:
    imported: List[ImportedRecord] = field(default_factory=list)
    duplicates: List[DuplicateRecord] = field(default_factory=list)
    rejected: List[RejectedRecord] = field(default_factory=list)
    cleaned_prices: Dict[str, Decimal] = field(default_factory=dict)


def normalize_tier_name(raw_name: str) -> str:
    """Trim whitespace, unify casing. 'GOLD' / 'gold' / 'Gold' -> 'Gold'."""
    return raw_name.strip().title()


def parse_price(raw_price: str) -> Decimal:
    """Parse '150', '150.00', '₹150', '₹150.00' into Decimal.

    Raises ValueError with a clear reason on blank, negative, or
    unparseable input.
    """
    if raw_price is None or str(raw_price).strip() == "":
        raise ValueError("blank price")

    cleaned = str(raw_price).strip().replace("₹", "").replace(",", "").strip()

    try:
        price = Decimal(cleaned)
    except InvalidOperation:
        raise ValueError(f"invalid price format: {raw_price!r}")

    if price < Decimal("0"):
        raise ValueError("negative price")

    return price.quantize(Decimal("0.01"))


def import_price_list(records: List[Dict[str, str]]) -> ImportReport:
    """Clean a messy list of {'name': ..., 'price': ...} records.

    Duplicate rule (assumption, not specified by the problem statement):
    first valid occurrence of a normalized tier name wins. Same-price
    repeats are logged as duplicates (ignored). Conflicting-price repeats
    are logged as duplicates and rejected, keeping the first price.
    """
    report = ImportReport()
    seen_prices: Dict[str, Decimal] = {}      # key -> price
    seen_display_names: Dict[str, str] = {}   # key -> normalized display name

    for record in records:
        original_name = record.get("name", "")
        raw_price = record.get("price", "")

        if not str(original_name).strip():
            report.rejected.append(
                RejectedRecord(original_name, raw_price, "blank tier name")
            )
            continue

        normalized_name = normalize_tier_name(original_name)
        key = normalized_name.lower()

        try:
            price = parse_price(raw_price)
        except ValueError as e:
            report.rejected.append(
                RejectedRecord(original_name, raw_price, str(e))
            )
            continue

        if key not in seen_prices:
            seen_prices[key] = price
            seen_display_names[key] = normalized_name
            report.imported.append(
                ImportedRecord(original_name, normalized_name, raw_price, price)
            )
        else:
            existing_price = seen_prices[key]
            if price == existing_price:
                report.duplicates.append(
                    DuplicateRecord(
                        original_name, normalized_name, raw_price,
                        "duplicate tier, same price — ignored",
                    )
                )
            else:
                report.duplicates.append(
                    DuplicateRecord(
                        original_name, normalized_name, raw_price,
                        "conflicting price — kept first occurrence",
                    )
                )

    report.cleaned_prices = {
        seen_display_names[key]: price for key, price in seen_prices.items()
    }
    return report