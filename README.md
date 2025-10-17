# Trade Execution System (TES)

TES is a lightweight research environment for building and evaluating automated
crypto trading strategies based on the Exponential Moving Average (EMA)
indicator.  The project contains a small collection of reusable strategy
components together with utility scripts that make it easy to explore new ideas
in a reproducible manner.

## Project layout

```
TES/
├── backtester.ipynb          # Interactive notebook that demonstrates the EMA backtester
├── clear_cache.py            # Helper script to remove cached market data
├── requirements.txt          # Python dependencies for notebooks and scripts
├── strategies/               # Collection of trading strategy building blocks
│   ├── ema_cross_01/         # Simple experimentation notebook for the initial EMA cross idea
│   └── ema_cross_02/         # Modular implementation used by backtesting utilities
└── package.json              # Convenience scripts for linting / formatting (optional)
```

## Quick start

1. Create and activate a Python environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Open `backtester.ipynb` in JupyterLab or VS Code to walk through the sample
   workflow.  The notebook shows how to download OHLCV candles, compute EMA
   signals, and simulate trades.
4. Adjust the configuration variables in `strategies/ema_cross_02/tuples_and_variables.py`
   to match your preferred market and trading parameters.

## Strategy overview

The core of the repository is an EMA crossover strategy implemented in
`strategies/ema_cross_02/ema_cross_class.py`.  The strategy monitors the
relationship between a fast EMA and a slow EMA to generate long/flat signals.
Risk management is configurable via percentage-based stop-loss and take-profit
levels.  Support functions for computing indicators and structuring the
backtest outputs live in `dos_ind_cart_funcs.py`.

## Data caching

The included `clear_cache.py` script removes temporary parquet or CSV files that
may accumulate while experimenting with new strategies.  It is safe to run the
script at any time; cached files will be re-created automatically the next time
market data is downloaded.

## Development

The optional `package.json` exposes a few convenience commands for formatting
and linting using popular Python tooling such as Ruff and Black.  These commands
are not required to use TES, but they provide a consistent development
experience when collaborating on strategy research.

