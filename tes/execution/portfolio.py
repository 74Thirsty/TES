"""Portfolio accounting helpers for TES backtests and live trading."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from math import isfinite

from .orders import OrderSide, Position, Trade


@dataclass(slots=True)
class PortfolioSnapshot:
    timestamp: datetime
    equity: float
    cash: float
    position_quantity: float
    position_value: float
    unrealised_pnl: float
    realised_pnl: float
    gross_exposure: float


@dataclass(slots=True)
class Portfolio:
    """Simple single-asset portfolio supporting long/flat exposure."""

    cash: float
    position: Position = field(default_factory=Position)
    trade_history: List[Trade] = field(default_factory=list)
    snapshots: List[PortfolioSnapshot] = field(default_factory=list)
    realised_pnl: float = 0.0

    def _record_snapshot(self, timestamp: datetime, mark_price: float) -> None:
        if not isfinite(mark_price) or mark_price <= 0:
            raise ValueError("Mark price must be a positive, finite number")

        equity = self.cash + self.position.market_value(mark_price)
        gross_exposure = abs(self.position.quantity) * mark_price
        snapshot = PortfolioSnapshot(
            timestamp=timestamp,
            equity=equity,
            cash=self.cash,
            position_quantity=self.position.quantity,
            position_value=self.position.market_value(mark_price),
            unrealised_pnl=self.position.unrealised_pnl(mark_price),
            realised_pnl=self.realised_pnl,
            gross_exposure=gross_exposure,
        )
        self.snapshots.append(snapshot)

    def process_trade(self, trade: Trade) -> None:
        if trade.quantity <= 0:
            raise ValueError("Trade quantity must be positive")

        execution_price = trade.execution_price()
        notional = execution_price * trade.quantity
        pre_trade_average_price = self.position.average_price
        pre_trade_quantity = self.position.quantity

        if trade.side == OrderSide.BUY:
            total_cost = notional + trade.fee
            if total_cost - self.cash > 1e-9:
                raise ValueError("Insufficient cash to execute buy trade")
            self.cash -= total_cost
        else:
            if trade.quantity - pre_trade_quantity > 1e-9:
                raise ValueError("Cannot sell more than current position quantity")
            proceeds = notional - trade.fee
            self.cash += proceeds

        self.position.apply_trade(trade)
        self.trade_history.append(trade)

        if trade.side == OrderSide.SELL:
            unit_fee = trade.fee / trade.quantity
            realised = ((execution_price - unit_fee) - pre_trade_average_price) * trade.quantity
            self.realised_pnl += realised

    def mark_to_market(self, timestamp: datetime, mark_price: float) -> None:
        self._record_snapshot(timestamp, mark_price)

    def total_equity(self) -> float:
        if not self.snapshots:
            return self.cash
        return self.snapshots[-1].equity
