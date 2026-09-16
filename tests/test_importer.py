"""Tests for pricing.importer"""

from decimal import Decimal
import pytest

from pricing.importer import import_price_list, parse_price, normalize_tier_name
from pricing.engine import PricingConfig, price_single_ticket, DEFAULT_CONFIG


# Normal valid records
def test_valid_records_imported():
    records = [
        {"name": "Silver", "price": "150"},
        {"name": "Gold", "price": "250.00"},
    ]
    report = import_price_list(records)
    assert len(report.imported) == 2
    assert report.cleaned_prices["Silver"] == Decimal("150.00")
    assert report.cleaned_prices["Gold"] == Decimal("250.00")


# Case-insensitive duplicates
def test_case_insensitive_duplicate_names_merge():
    records = [
        {"name": "Gold", "price": "250"},
        {"name": "GOLD", "price": "250"},
        {"name": "gold", "price": "250"},
    ]
    report = import_price_list(records)
    assert len(report.imported) == 1
    assert len(report.duplicates) == 2
    assert "Gold" in report.cleaned_prices


# Duplicate, same price
def test_duplicate_same_price_logged_as_duplicate_not_rejected():
    records = [
        {"name": "Silver", "price": "150"},
        {"name": "silver", "price": "150.00"},
    ]
    report = import_price_list(records)
    assert len(report.rejected) == 0
    assert len(report.duplicates) == 1
    assert report.duplicates[0].reason == "duplicate tier, same price — ignored"


# Duplicate, conflicting price
def test_duplicate_conflicting_price_keeps_first():
    records = [
        {"name": "Recliner", "price": "400"},
        {"name": "RECLINER", "price": "450"},
    ]
    report = import_price_list(records)
    assert report.cleaned_prices["Recliner"] == Decimal("400.00")
    assert len(report.duplicates) == 1
    assert report.duplicates[0].reason == "conflicting price — kept first occurrence"


# ₹ currency format
def test_rupee_symbol_price_parsed():
    assert parse_price("₹150") == Decimal("150.00")
    assert parse_price("₹150.00") == Decimal("150.00")


# Decimal format
def test_decimal_price_parsed():
    assert parse_price("150.00") == Decimal("150.00")
    assert parse_price("150") == Decimal("150.00")


# Blank price
def test_blank_price_rejected():
    records = [{"name": "Silver", "price": ""}]
    report = import_price_list(records)
    assert len(report.rejected) == 1
    assert report.rejected[0].reason == "blank price"


def test_missing_price_key_rejected():
    records = [{"name": "Silver"}]
    report = import_price_list(records)
    assert len(report.rejected) == 1
    assert report.rejected[0].reason == "blank price"


# Negative price
def test_negative_price_rejected():
    records = [{"name": "Gold", "price": "-100"}]
    report = import_price_list(records)
    assert len(report.rejected) == 1
    assert report.rejected[0].reason == "negative price"


# Invalid price
def test_invalid_price_format_rejected():
    records = [{"name": "Gold", "price": "abc"}]
    report = import_price_list(records)
    assert len(report.rejected) == 1
    assert "invalid price format" in report.rejected[0].reason


# Mixed valid and invalid
def test_mixed_valid_and_invalid_records():
    records = [
        {"name": "Silver", "price": "150"},
        {"name": "Gold", "price": ""},
        {"name": "Recliner", "price": "-50"},
        {"name": "VIP", "price": "abc"},
        {"name": "Balcony", "price": "₹300.00"},
    ]
    report = import_price_list(records)
    assert len(report.imported) == 2  # Silver, Balcony
    assert len(report.rejected) == 3  # Gold, Recliner, VIP


# Empty input
def test_empty_input_produces_empty_report():
    report = import_price_list([])
    assert report.imported == []
    assert report.duplicates == []
    assert report.rejected == []
    assert report.cleaned_prices == {}


# Final cleaned price list
def test_cleaned_price_list_structure():
    records = [
        {"name": "silver", "price": "150"},
        {"name": "GOLD", "price": "₹250.00"},
    ]
    report = import_price_list(records)
    assert report.cleaned_prices == {
        "Silver": Decimal("150.00"),
        "Gold": Decimal("250.00"),
    }


# Import/dedup/rejection report completeness
def test_report_categorizes_every_input_record():
    records = [
        {"name": "Silver", "price": "150"},
        {"name": "silver", "price": "150"},       # duplicate, same price
        {"name": "Gold", "price": "-10"},          # rejected
        {"name": "", "price": "100"},              # rejected, blank name
    ]
    report = import_price_list(records)
    total_seen = len(report.imported) + len(report.duplicates) + len(report.rejected)
    assert total_seen == len(records)


# Integration: cleaned prices usable directly by pricing engine
def test_cleaned_prices_plug_into_pricing_engine():
    records = [
        {"name": "silver", "price": "150"},
        {"name": "GOLD", "price": "250.00"},
        {"name": "Recliner", "price": "₹400"},
    ]
    report = import_price_list(records)

    config = PricingConfig(
        tier_prices=report.cleaned_prices,
        festival_discount_per_ticket=DEFAULT_CONFIG.festival_discount_per_ticket,
        member_discount_percent=DEFAULT_CONFIG.member_discount_percent,
        member_discount_cap=DEFAULT_CONFIG.member_discount_cap,
        convenience_fee_per_ticket=DEFAULT_CONFIG.convenience_fee_per_ticket,
        gst_percent=DEFAULT_CONFIG.gst_percent,
    )

    result = price_single_ticket("Silver", is_member=False, config=config)
    assert result.base_price == Decimal("150.00")