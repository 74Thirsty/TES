"""Utility helpers for cleaning cached market data.

The research notebooks may create temporary CSV or Parquet files inside the
`data/` directory when experimenting with new trading strategies.  The files are
safe to remove at any time.  This script provides a convenient command-line
interface to purge those caches.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def clear_cache(path: Path) -> list[Path]:
    """Delete cache files under *path*.

    Parameters
    ----------
    path:
        Root directory whose contents should be deleted.  The directory itself
        will be kept in place.

    Returns
    -------
    list[Path]
        The list of files that were successfully removed.
    """

    removed: list[Path] = []
    if not path.exists():
        return removed

    for cached_file in path.glob("**/*"):
        if cached_file.is_file():
            cached_file.unlink()
            removed.append(cached_file)
    return removed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clear cached TES market data")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("data"),
        help="Directory that stores cached market data (default: ./data)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    removed = clear_cache(args.path)
    if removed:
        print("Removed the following cached files:")
        for item in removed:
            print(f" - {item}")
    else:
        print("No cached files found – nothing to remove.")


if __name__ == "__main__":
    main()
