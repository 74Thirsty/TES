import unittest
from pathlib import Path

import pandas as pd

from strategies.ema_cross_02.ema_cross_class import EMACrossStrategy
from tes.execution.engine import ExecutionEngine


class ExecutionEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        csv_path = Path(__file__).resolve().parent.parent / "data" / "sample_candles.csv"
        self.frame = pd.read_csv(csv_path)
        self.frame["timestamp"] = pd.to_datetime(self.frame["timestamp"])

    def test_backtest_produces_equity_curve(self) -> None:
        strategy = EMACrossStrategy(fast_window=3, slow_window=6)
        engine = ExecutionEngine(strategy=strategy, initial_balance=10_000.0)
        result = engine.run_backtest(self.frame)

        self.assertGreater(len(result.equity_curve), 0)
        self.assertGreaterEqual(result.metrics.trade_count, 0)
        self.assertIsNotNone(result.metrics.total_return)
        self.assertIsNotNone(result.metrics.max_drawdown)

    def test_invalid_max_position_pct(self) -> None:
        strategy = EMACrossStrategy(fast_window=3, slow_window=6)
        with self.assertRaises(ValueError):
            ExecutionEngine(strategy=strategy, max_position_pct=1.5)

    def test_empty_candles_raises(self) -> None:
        strategy = EMACrossStrategy(fast_window=3, slow_window=6)
        engine = ExecutionEngine(strategy=strategy)
        with self.assertRaises(ValueError):
            engine.run_backtest(self.frame.iloc[0:0])


if __name__ == "__main__":
    unittest.main()
