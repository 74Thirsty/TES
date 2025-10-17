"""Indicator and cartesian-product helper functions for EMA strategies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import numpy as np
import pandas as pd


def compute_ema(series: Iterable[float], window: int) -> pd.Series:
    """Return the exponential moving average for *series* using *window* periods."""

    return pd.Series(series, copy=False).ewm(span=window, adjust=False).mean()


def compute_stop_levels(
    price: float,
    *,
    direction: bool,
    stop_loss_pct: Optional[float],
    take_profit_pct: Optional[float],
) -> tuple[Optional[float], Optional[float]]:
    """Calculate stop-loss and take-profit price levels."""

    stop_loss = None
    take_profit = None

    if stop_loss_pct is not None:
        if direction:
            stop_loss = price * (1 - stop_loss_pct)
        else:
            stop_loss = price * (1 + stop_loss_pct)

    if take_profit_pct is not None:
        if direction:
            take_profit = price * (1 + take_profit_pct)
        else:
            take_profit = price * (1 - take_profit_pct)

    return stop_loss, take_profit


@dataclass(slots=True)
class OptimizationResult:
    """Result container for hyper-parameter sweeps."""

    fast_window: int
    slow_window: int
    stop_loss_pct: Optional[float]
    take_profit_pct: Optional[float]
    sharpe_ratio: float


def evaluate_parameter_grid(
    candles: pd.DataFrame,
    parameter_grid: Iterable[tuple[int, int, Optional[float], Optional[float]]],
    evaluator,
) -> list[OptimizationResult]:
    """Evaluate combinations of EMA parameters and collect the results."""

    results: list[OptimizationResult] = []
    for fast_window, slow_window, stop_loss, take_profit in parameter_grid:
        stats = evaluator(
            candles,
            fast_window=fast_window,
            slow_window=slow_window,
            stop_loss_pct=stop_loss,
            take_profit_pct=take_profit,
        )
        results.append(
            OptimizationResult(
                fast_window=fast_window,
                slow_window=slow_window,
                stop_loss_pct=stop_loss,
                take_profit_pct=take_profit,
                sharpe_ratio=float(stats["sharpe_ratio"]),
            )
        )
    return results
