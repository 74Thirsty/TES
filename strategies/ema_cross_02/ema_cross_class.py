"""EMA crossover strategy implementation.

The strategy keeps track of two exponential moving averages (EMAs) – a *fast*
window and a *slow* window – and emits long/flat signals when the fast EMA
crosses above or below the slow EMA.  The class is deliberately lightweight so
that it can be reused in notebooks, backtesting pipelines, or live execution
adapters.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

import numpy as np
import pandas as pd

from .dos_ind_cart_funcs import compute_ema, compute_stop_levels


@dataclass(slots=True)
class EMASignal:
    """Represents a single trading signal produced by the strategy."""

    timestamp: datetime
    price: float
    direction: int  # +1 for long, 0 for flat
    fast_ema: float
    slow_ema: float
    stop_loss: Optional[float]
    take_profit: Optional[float]


class EMACrossStrategy:
    """Compute EMA crossover signals for OHLCV data."""

    def __init__(
        self,
        fast_window: int = 12,
        slow_window: int = 26,
        stop_loss_pct: Optional[float] = 0.02,
        take_profit_pct: Optional[float] = 0.04,
    ) -> None:
        if fast_window <= 0 or slow_window <= 0:
            raise ValueError("EMA window sizes must be positive integers")
        if fast_window >= slow_window:
            raise ValueError("Fast window must be smaller than slow window")

        self.fast_window = fast_window
        self.slow_window = slow_window
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def generate_signals(self, candles: pd.DataFrame) -> list[EMASignal]:
        """Generate EMA crossover signals from OHLCV candles.

        The input frame must contain at least the columns ``close`` and
        ``timestamp``.  Additional columns are ignored.
        """

        required_columns = {"close", "timestamp"}
        missing = required_columns.difference(candles.columns)
        if missing:
            raise KeyError(f"Missing required candle columns: {sorted(missing)}")

        df = candles.copy()
        df["fast_ema"] = compute_ema(df["close"], self.fast_window)
        df["slow_ema"] = compute_ema(df["close"], self.slow_window)
        df.dropna(inplace=True)

        direction = np.where(df["fast_ema"] > df["slow_ema"], 1, 0)
        cross = direction.astype(int).diff().fillna(0) != 0

        signals: list[EMASignal] = []
        for idx, row in df.loc[cross].iterrows():
            price = float(row["close"])
            stop_loss, take_profit = compute_stop_levels(
                price,
                direction=row["fast_ema"] > row["slow_ema"],
                stop_loss_pct=self.stop_loss_pct,
                take_profit_pct=self.take_profit_pct,
            )
            signals.append(
                EMASignal(
                    timestamp=_ensure_timestamp(row["timestamp"]),
                    price=price,
                    direction=int(row["fast_ema"] > row["slow_ema"]),
                    fast_ema=float(row["fast_ema"]),
                    slow_ema=float(row["slow_ema"]),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                )
            )
        return signals

    def to_dataframe(self, signals: Iterable[EMASignal]) -> pd.DataFrame:
        """Convert a sequence of :class:`EMASignal` objects into a DataFrame."""

        rows = [
            {
                "timestamp": signal.timestamp,
                "price": signal.price,
                "direction": signal.direction,
                "fast_ema": signal.fast_ema,
                "slow_ema": signal.slow_ema,
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
            }
            for signal in signals
        ]
        return pd.DataFrame(rows)


def _ensure_timestamp(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, (np.datetime64, pd.Timestamp)):
        return pd.Timestamp(value).to_pydatetime()
    raise TypeError(f"Unsupported timestamp type: {type(value)!r}")
