"""Configuration helpers for the EMA crossover strategy."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable, Optional


@dataclass(frozen=True)
class StrategyConfig:
    symbol: str
    timeframe: str
    fast_window: int
    slow_window: int
    stop_loss_pct: Optional[float]
    take_profit_pct: Optional[float]


DEFAULT_CONFIG = StrategyConfig(
    symbol="BTC/USDT",
    timeframe="1h",
    fast_window=12,
    slow_window=26,
    stop_loss_pct=0.02,
    take_profit_pct=0.04,
)


def parameter_grid(
    fast_windows: Iterable[int],
    slow_windows: Iterable[int],
    stop_loss: Iterable[Optional[float]],
    take_profit: Iterable[Optional[float]],
):
    """Yield combinations of strategy parameters."""

    for fast, slow, sl, tp in product(fast_windows, slow_windows, stop_loss, take_profit):
        if fast >= slow:
            continue
        yield fast, slow, sl, tp
