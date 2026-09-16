"""Core pricing engine for multiplex ticket booking.

All money is decimal.Decimal, rounded to 2 places (rupees.paise).
Floating point is never used for money.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict

TWO_PLACES = Decimal("0.01")


def round_money(value: Decimal) -> Decimal:
    """Round to nearest paisa, standard round-half-up."""
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


@dataclass
class PricingConfig:
    """All business-rule numbers live here. Change values, not logic."""
    tier_prices: Dict[str, Decimal]
    festival_discount_per_ticket: Decimal
    member_discount_percent: Decimal
    member_discount_cap: Decimal
    convenience_fee_per_ticket: Decimal
    gst_percent: Decimal


DEFAULT_CONFIG = PricingConfig(
    tier_prices={
        "Silver": Decimal("150.00"),
        "Gold": Decimal("250.00"),
        "Recliner": Decimal("400.00"),
    },
    festival_discount_per_ticket=Decimal("50.00"),
    member_discount_percent=Decimal("10"),
    member_discount_cap=Decimal("100.00"),
    convenience_fee_per_ticket=Decimal("20.00"),
    gst_percent=Decimal("18"),
)


@dataclass
class Tier:
    name: str
    available_seats: int


class PricingError(ValueError):
    """Invalid tier, sold out, or bad quantity."""


@dataclass
class TicketBreakdown:
    base_price: Decimal
    festival_discount: Decimal
    price_after_festival: Decimal
    member_discount: Decimal
    price_after_member: Decimal
    convenience_fee: Decimal
    taxable_amount: Decimal
    gst: Decimal
    final_price: Decimal


@dataclass
class BillBreakdown:
    tier: str
    quantity: int
    per_ticket: TicketBreakdown
    total_base_price: Decimal
    total_festival_discount: Decimal
    total_member_discount: Decimal
    total_convenience_fee: Decimal
    total_gst: Decimal
    grand_total: Decimal


def price_single_ticket(
    tier_name: str,
    is_member: bool,
    config: PricingConfig = DEFAULT_CONFIG,
) -> TicketBreakdown:
    """Line-by-line price for one ticket."""
    if tier_name not in config.tier_prices:
        raise PricingError(f"Unknown tier: {tier_name}")

    base_price = config.tier_prices[tier_name]

    # 1. Festival discount (flat, per ticket)
    festival_discount = round_money(config.festival_discount_per_ticket)
    price_after_festival = round_money(base_price - festival_discount)
    if price_after_festival < Decimal("0"):
        price_after_festival = Decimal("0.00")
        festival_discount = base_price

    # 2. Member discount (% of post-festival price, capped)
    member_discount = Decimal("0.00")
    if is_member:
        raw = price_after_festival * config.member_discount_percent / Decimal("100")
        member_discount = round_money(raw)
        if member_discount > config.member_discount_cap:
            member_discount = config.member_discount_cap
    price_after_member = round_money(price_after_festival - member_discount)

    # 3. Convenience fee (after discounts)
    convenience_fee = round_money(config.convenience_fee_per_ticket)

    # 4. GST on (discounted price + convenience fee)
    taxable_amount = round_money(price_after_member + convenience_fee)
    gst = round_money(taxable_amount * config.gst_percent / Decimal("100"))

    final_price = round_money(taxable_amount + gst)

    return TicketBreakdown(
        base_price=base_price,
        festival_discount=festival_discount,
        price_after_festival=price_after_festival,
        member_discount=member_discount,
        price_after_member=price_after_member,
        convenience_fee=convenience_fee,
        taxable_amount=taxable_amount,
        gst=gst,
        final_price=final_price,
    )


def price_booking(
    tier_name: str,
    quantity: int,
    is_member: bool,
    tiers: Dict[str, Tier],
    config: PricingConfig = DEFAULT_CONFIG,
) -> BillBreakdown:
    """Price `quantity` tickets of one tier, after availability checks."""
    if quantity <= 0:
        raise PricingError("Quantity must be a positive integer")
    if tier_name not in tiers:
        raise PricingError(f"Unknown tier: {tier_name}")

    tier = tiers[tier_name]
    if tier.available_seats <= 0:
        raise PricingError(f"{tier_name} is sold out")
    if tier.available_seats < quantity:
        raise PricingError(
            f"Only {tier.available_seats} seat(s) left in {tier_name}, "
            f"requested {quantity}"
        )

    per_ticket = price_single_ticket(tier_name, is_member, config)

    return BillBreakdown(
        tier=tier_name,
        quantity=quantity,
        per_ticket=per_ticket,
        total_base_price=round_money(per_ticket.base_price * quantity),
        total_festival_discount=round_money(per_ticket.festival_discount * quantity),
        total_member_discount=round_money(per_ticket.member_discount * quantity),
        total_convenience_fee=round_money(per_ticket.convenience_fee * quantity),
        total_gst=round_money(per_ticket.gst * quantity),
        grand_total=round_money(per_ticket.final_price * quantity),
    )