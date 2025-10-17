"""Market data feed abstractions used by TES."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Iterator

import pandas as pd


@dataclass(slots=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class CandleFeed(Iterable[Candle]):
    """Abstract base class for candle feeds."""

    def __iter__(self) -> Iterator[Candle]:
        raise NotImplementedError


class DataFrameFeed(CandleFeed):
    """Yield candles from a pandas DataFrame."""

    def __init__(self, frame: pd.DataFrame, timestamp_column: str = "timestamp") -> None:
        self.frame = frame.copy()
        self.timestamp_column = timestamp_column
        required = {timestamp_column, "open", "high", "low", "close", "volume"}
        missing = required.difference(self.frame.columns)
        if missing:
            raise KeyError(f"Missing required columns: {sorted(missing)}")

    def __iter__(self) -> Iterator[Candle]:
        for _, row in self.frame.iterrows():
            yield Candle(
                timestamp=_ensure_timestamp(row[self.timestamp_column]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            )


def _ensure_timestamp(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, (pd.Timestamp,)):
        return value.to_pydatetime()
    return pd.to_datetime(value).to_pydatetime()
