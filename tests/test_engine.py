"""Test suite for pricing.engine"""

from decimal import Decimal
import pytest

from pricing.engine import (
    price_single_ticket,
    price_booking,
    round_money,
    PricingConfig,
    PricingError,
    Tier,
    DEFAULT_CONFIG,
)


def make_tiers(silver=5, gold=5, recliner=5):
    return {
        "Silver": Tier("Silver", silver),
        "Gold": Tier("Gold", gold),
        "Recliner": Tier("Recliner", recliner),
    }


# 1. Tier pricing (base prices only, no discounts, non-member)
def test_silver_base_pricing():
    r = price_single_ticket("Silver", is_member=False)
    assert r.base_price == Decimal("150.00")


def test_gold_base_pricing():
    r = price_single_ticket("Gold", is_member=False)
    assert r.base_price == Decimal("250.00")


def test_recliner_base_pricing():
    r = price_single_ticket("Recliner", is_member=False)
    assert r.base_price == Decimal("400.00")


# 2. Multiple tickets, mixed tiers (two separate bookings, summed manually)
def test_multiple_tickets_mixed_tiers():
    tiers = make_tiers()
    silver_bill = price_booking("Silver", 2, is_member=False, tiers=tiers)
    gold_bill = price_booking("Gold", 3, is_member=False, tiers=tiers)
    combined_total = silver_bill.grand_total + gold_bill.grand_total
    assert silver_bill.quantity == 2
    assert gold_bill.quantity == 3
    assert combined_total == silver_bill.grand_total + gold_bill.grand_total


# 3. Festival discount
def test_festival_discount_applied():
    r = price_single_ticket("Silver", is_member=False)
    assert r.festival_discount == Decimal("50.00")
    assert r.price_after_festival == Decimal("100.00")


def test_festival_discount_capped_at_base_price():
    config = PricingConfig(
        tier_prices={"Silver": Decimal("30.00")},
        festival_discount_per_ticket=Decimal("50.00"),
        member_discount_percent=Decimal("10"),
        member_discount_cap=Decimal("100.00"),
        convenience_fee_per_ticket=Decimal("20.00"),
        gst_percent=Decimal("18"),
    )
    r = price_single_ticket("Silver", is_member=False, config=config)
    assert r.price_after_festival == Decimal("0.00")
    assert r.festival_discount == Decimal("30.00")


# 4. Member discount
def test_member_discount_applied():
    r = price_single_ticket("Silver", is_member=True)
    assert r.member_discount == Decimal("10.00")
    assert r.price_after_member == Decimal("90.00")


def test_non_member_gets_no_member_discount():
    r = price_single_ticket("Silver", is_member=False)
    assert r.member_discount == Decimal("0.00")


# 5. Member discount cap
def test_member_discount_cap_enforced():
    config = PricingConfig(
        tier_prices={"Recliner": Decimal("2000.00")},
        festival_discount_per_ticket=Decimal("50.00"),
        member_discount_percent=Decimal("10"),
        member_discount_cap=Decimal("100.00"),
        convenience_fee_per_ticket=Decimal("20.00"),
        gst_percent=Decimal("18"),
    )
    r = price_single_ticket("Recliner", is_member=True, config=config)
    # 10% of (2000-50) = 195, but cap is 100
    assert r.member_discount == Decimal("100.00")


# 6. Discount order: festival first, member on post-festival price
def test_discount_order_festival_then_member():
    r = price_single_ticket("Silver", is_member=True)
    # base 150 - festival 50 = 100; member 10% of 100 = 10, not 10% of 150
    assert r.price_after_festival == Decimal("100.00")
    assert r.member_discount == Decimal("10.00")


# 7. Convenience fee
def test_convenience_fee_added_after_discounts():
    r = price_single_ticket("Silver", is_member=True)
    assert r.convenience_fee == Decimal("20.00")
    assert r.taxable_amount == r.price_after_member + r.convenience_fee


# 8. GST
def test_gst_on_discounted_price_plus_fee():
    r = price_single_ticket("Silver", is_member=True)
    # taxable = 90 + 20 = 110; GST 18% = 19.80
    assert r.taxable_amount == Decimal("110.00")
    assert r.gst == Decimal("19.80")


# 9. Exact paisa-level calculation, full breakdown
def test_full_breakdown_exact_paisa():
    r = price_single_ticket("Silver", is_member=True)
    assert r.base_price == Decimal("150.00")
    assert r.festival_discount == Decimal("50.00")
    assert r.price_after_festival == Decimal("100.00")
    assert r.member_discount == Decimal("10.00")
    assert r.price_after_member == Decimal("90.00")
    assert r.convenience_fee == Decimal("20.00")
    assert r.taxable_amount == Decimal("110.00")
    assert r.gst == Decimal("19.80")
    assert r.final_price == Decimal("129.80")


# 10. Round-half-up behavior
def test_round_half_up_rounds_up_at_half_paisa():
    assert round_money(Decimal("10.005")) == Decimal("10.01")
    assert round_money(Decimal("10.015")) == Decimal("10.02")
    assert round_money(Decimal("10.004")) == Decimal("10.00")
    assert round_money(Decimal("10.006")) == Decimal("10.01")


def test_rounding_applied_with_fractional_config():
    config = PricingConfig(
        tier_prices={"Silver": Decimal("99.995")},
        festival_discount_per_ticket=Decimal("0.00"),
        member_discount_percent=Decimal("0"),
        member_discount_cap=Decimal("0.00"),
        convenience_fee_per_ticket=Decimal("0.00"),
        gst_percent=Decimal("0"),
    )
    r = price_single_ticket("Silver", is_member=False, config=config)
    assert r.price_after_festival == Decimal("100.00")  # 99.995 rounds up


# 11. Sold-out tiers
def test_sold_out_tier_raises_error():
    tiers = make_tiers(gold=0)
    with pytest.raises(PricingError, match="sold out"):
        price_booking("Gold", 1, is_member=False, tiers=tiers)


# 12. Insufficient available seats
def test_insufficient_seats_raises_error():
    tiers = make_tiers(silver=1)
    with pytest.raises(PricingError, match="Only 1 seat"):
        price_booking("Silver", 2, is_member=False, tiers=tiers)


# 13. Invalid tier
def test_invalid_tier_name_raises_error():
    tiers = make_tiers()
    with pytest.raises(PricingError, match="Unknown tier"):
        price_booking("Diamond", 1, is_member=False, tiers=tiers)


def test_invalid_tier_in_price_single_ticket():
    with pytest.raises(PricingError, match="Unknown tier"):
        price_single_ticket("Diamond", is_member=False)


# 14. Invalid quantity
def test_zero_quantity_raises_error():
    tiers = make_tiers()
    with pytest.raises(PricingError, match="positive integer"):
        price_booking("Silver", 0, is_member=False, tiers=tiers)


def test_negative_quantity_raises_error():
    tiers = make_tiers()
    with pytest.raises(PricingError, match="positive integer"):
        price_booking("Silver", -1, is_member=False, tiers=tiers)


def test_non_integer_quantity_raises_error():
    tiers = make_tiers()
    with pytest.raises(PricingError, match="positive integer"):
        price_booking("Silver", 2.5, is_member=False, tiers=tiers)


def test_boolean_quantity_raises_error():
    tiers = make_tiers()
    with pytest.raises(PricingError, match="positive integer"):
        price_booking("Silver", True, is_member=False, tiers=tiers)


# 15. Member and non-member bookings
def test_member_booking_totals():
    tiers = make_tiers()
    bill = price_booking("Silver", 1, is_member=True, tiers=tiers)
    assert bill.total_member_discount == Decimal("10.00")


def test_non_member_booking_totals():
    tiers = make_tiers()
    bill = price_booking("Silver", 1, is_member=False, tiers=tiers)
    assert bill.total_member_discount == Decimal("0.00")


# 16. Complete end-to-end billing
def test_end_to_end_booking_totals():
    tiers = make_tiers()
    bill = price_booking("Recliner", 3, is_member=True, tiers=tiers)
    assert bill.quantity == 3
    assert bill.total_base_price == Decimal("400.00") * 3
    assert bill.grand_total == bill.per_ticket.final_price * 3


# 17. Edge cases
def test_exact_remaining_seats_can_be_booked():
    tiers = make_tiers(silver=2)
    bill = price_booking("Silver", 2, is_member=False, tiers=tiers)
    assert bill.quantity == 2


def test_single_ticket_booking():
    tiers = make_tiers()
    bill = price_booking("Gold", 1, is_member=False, tiers=tiers)
    assert bill.quantity == 1


def test_large_quantity_booking():
    tiers = make_tiers(recliner=100)
    bill = price_booking("Recliner", 100, is_member=True, tiers=tiers)
    assert bill.quantity == 100