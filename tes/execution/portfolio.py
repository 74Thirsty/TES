"""Portfolio accounting helpers for TES backtests and live trading."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from .orders import OrderSide, Position, Trade


@dataclass(slots=True)
class PortfolioSnapshot:
    timestamp: datetime
    equity: float
    cash: float
    position_quantity: float
    position_value: float
    unrealised_pnl: float


@dataclass(slots=True)
class Portfolio:
    """Simple single-asset portfolio supporting long/flat exposure."""

    cash: float
    position: Position = field(default_factory=Position)
    trade_history: List[Trade] = field(default_factory=list)
    snapshots: List[PortfolioSnapshot] = field(default_factory=list)

    def _record_snapshot(self, timestamp: datetime, mark_price: float) -> None:
        equity = self.cash + self.position.market_value(mark_price)
        snapshot = PortfolioSnapshot(
            timestamp=timestamp,
            equity=equity,
            cash=self.cash,
            position_quantity=self.position.quantity,
            position_value=self.position.market_value(mark_price),
            unrealised_pnl=self.position.unrealised_pnl(mark_price),
        )
        self.snapshots.append(snapshot)

    def process_trade(self, trade: Trade) -> None:
        execution_price = trade.execution_price()
        notional = execution_price * trade.quantity
        cost = notional + trade.fee if trade.side == OrderSide.BUY else notional - trade.fee

        if trade.side == OrderSide.BUY:
            if cost > self.cash:
                raise ValueError("Insufficient cash to execute buy trade")
            self.cash -= cost
        else:
            self.cash += cost

        self.position.apply_trade(trade)
        self.trade_history.append(trade)

    def mark_to_market(self, timestamp: datetime, mark_price: float) -> None:
        self._record_snapshot(timestamp, mark_price)

    def total_equity(self) -> float:
        if not self.snapshots:
            return self.cash
        return self.snapshots[-1].equity
