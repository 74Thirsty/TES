import math
import unittest
from datetime import datetime
from pathlib import Path

import pandas as pd

from strategies.ema_cross_02.ema_cross_class import EMACrossStrategy
from tes.execution.engine import ExecutionEngine
from tes.execution.orders import OrderSide, Trade
from tes.execution.portfolio import Portfolio


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
        self.assertIn("realised_pnl", result.equity_curve.columns)
        self.assertIn("gross_exposure", result.equity_curve.columns)
        self.assertIsNotNone(result.metrics.sortino_ratio)
        self.assertFalse(math.isnan(result.metrics.win_rate))

    def test_invalid_max_position_pct(self) -> None:
        strategy = EMACrossStrategy(fast_window=3, slow_window=6)
        with self.assertRaises(ValueError):
            ExecutionEngine(strategy=strategy, max_position_pct=1.5)

    def test_empty_candles_raises(self) -> None:
        strategy = EMACrossStrategy(fast_window=3, slow_window=6)
        engine = ExecutionEngine(strategy=strategy)
        with self.assertRaises(ValueError):
            engine.run_backtest(self.frame.iloc[0:0])

    def test_missing_close_column_raises(self) -> None:
        strategy = EMACrossStrategy(fast_window=3, slow_window=6)
        engine = ExecutionEngine(strategy=strategy)
        bad_frame = self.frame.drop(columns=["close"])
        with self.assertRaises(ValueError):
            engine.run_backtest(bad_frame)

    def test_duplicate_timestamps_raises(self) -> None:
        strategy = EMACrossStrategy(fast_window=3, slow_window=6)
        engine = ExecutionEngine(strategy=strategy)
        duplicated = pd.concat([self.frame.iloc[:1], self.frame.iloc[:1], self.frame.iloc[1:]], ignore_index=True)
        with self.assertRaises(ValueError):
            engine.run_backtest(duplicated)

    def test_portfolio_realised_pnl_updates(self) -> None:
        portfolio = Portfolio(cash=1_000.0)
        buy_trade = Trade(
            timestamp=datetime.utcnow(),
            side=OrderSide.BUY,
            price=100.0,
            quantity=1.0,
        )
        portfolio.process_trade(buy_trade)

        sell_trade = Trade(
            timestamp=datetime.utcnow(),
            side=OrderSide.SELL,
            price=120.0,
            quantity=1.0,
        )
        portfolio.process_trade(sell_trade)

        self.assertAlmostEqual(portfolio.realised_pnl, 20.0, places=6)

    def test_portfolio_prevents_oversell(self) -> None:
        portfolio = Portfolio(cash=1_000.0)
        buy_trade = Trade(
            timestamp=datetime.utcnow(),
            side=OrderSide.BUY,
            price=50.0,
            quantity=1.0,
        )
        portfolio.process_trade(buy_trade)

        sell_trade = Trade(
            timestamp=datetime.utcnow(),
            side=OrderSide.SELL,
            price=50.0,
            quantity=2.0,
        )

        with self.assertRaises(ValueError):
            portfolio.process_trade(sell_trade)

    def test_negative_prices_raise(self) -> None:
        strategy = EMACrossStrategy(fast_window=3, slow_window=6)
        engine = ExecutionEngine(strategy=strategy)
        bad_frame = self.frame.copy()
        bad_frame.loc[0, "close"] = -10
        with self.assertRaises(ValueError):
            engine.run_backtest(bad_frame)


if __name__ == "__main__":
    unittest.main()
