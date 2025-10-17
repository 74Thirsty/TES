"""Order and trade primitives used by the TES execution engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class OrderSide(str, Enum):
    """Side of the market for an order."""

    BUY = "buy"
    SELL = "sell"


@dataclass(slots=True)
class Order:
    """Represents an intent to trade a specific quantity at a price."""

    timestamp: datetime
    side: OrderSide
    price: float
    quantity: float
    fee: float = 0.0

    def value(self) -> float:
        """Return the notional value of the order (price * quantity)."""

        return self.price * self.quantity


@dataclass(slots=True)
class Trade(Order):
    """Executed trade with realised cost basis."""

    slippage: float = 0.0

    def execution_price(self) -> float:
        """Return the price after applying slippage."""

        if self.side == OrderSide.BUY:
            return self.price * (1 + self.slippage)
        return self.price * (1 - self.slippage)


@dataclass(slots=True)
class Position:
    """Tracks the open exposure for a single trading pair."""

    quantity: float = 0.0
    average_price: float = 0.0

    def is_flat(self) -> bool:
        return self.quantity == 0

    def market_value(self, mark_price: float) -> float:
        return self.quantity * mark_price

    def apply_trade(self, trade: Trade) -> None:
        """Update the position with an executed trade."""

        if trade.side == OrderSide.BUY:
            new_notional = self.average_price * self.quantity + trade.execution_price() * trade.quantity
            self.quantity += trade.quantity
            if self.quantity:
                self.average_price = new_notional / self.quantity
        else:
            self.quantity -= trade.quantity
            if self.quantity <= 0:
                self.quantity = 0.0
                self.average_price = 0.0

    def unrealised_pnl(self, mark_price: float) -> float:
        if self.is_flat():
            return 0.0
        return (mark_price - self.average_price) * self.quantity
