"""
Core data models for the ticket pricing engine.
All monetary values are stored as integer paise to avoid floating-point
rounding errors. 1 rupee = 100 paise.
"""

from dataclasses import dataclass, field
from typing import List
from abc import ABC, abstractmethod


class SoldOutError(Exception):
    """Raised when a booking requests more seats than available in a tier."""
    pass


class InvalidBookingError(Exception):
    """Raised for any other invalid booking request."""
    pass


@dataclass
class SeatTier:
    name: str
    price_paise: int          # base price per seat, in paise
    available_seats: int

    def reserve(self, quantity: int) -> None:
        if quantity <= 0:
            raise InvalidBookingError(f"Quantity must be positive, got {quantity}")
        if quantity > self.available_seats:
            raise SoldOutError(
                f"Tier '{self.name}' has only {self.available_seats} seat(s) left, "
                f"requested {quantity}"
            )


@dataclass
class Show:
    show_id: str
    tiers: dict  # tier_name -> SeatTier

    def get_tier(self, tier_name: str) -> SeatTier:
        if tier_name not in self.tiers:
            raise InvalidBookingError(f"No such seat tier: '{tier_name}'")
        return self.tiers[tier_name]


class Offer(ABC):
    """Base class for all discount offers."""
    name: str

    @abstractmethod
    def apply(self, base_amount_paise: int) -> int:
        """Return the discount amount in paise (positive number)."""
        raise NotImplementedError


@dataclass
class FlatDiscount(Offer):
    amount_paise: int
    name: str = "Flat Festival Discount"

    def apply(self, base_amount_paise: int) -> int:
        return min(self.amount_paise, base_amount_paise)


@dataclass
class PercentDiscount(Offer):
    percent: float
    cap_paise: int
    name: str = "Member Discount"

    def apply(self, base_amount_paise: int) -> int:
        raw = (base_amount_paise * self.percent) / 100
        return min(int(round(raw)), self.cap_paise, base_amount_paise)


@dataclass
class PricingConfig:
    """Cinema-wide configurable rules — nothing hardcoded per show."""
    convenience_fee_per_ticket_paise: int
    gst_percent: float