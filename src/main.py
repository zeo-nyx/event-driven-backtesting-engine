"""CLI entrypoint for running the backtest."""

from __future__ import annotations

from pathlib import Path

from backtest import Backtest


def main() -> None:
    """Run a sample backtest and print summary metrics."""
    project_root = Path(__file__).resolve().parent.parent
    csv_dir = project_root / "data"

    backtest = Backtest(
        csv_dir=csv_dir,
        symbol_list=["AAPL"],
        initial_capital=100000.0,
        short_window=20,
        long_window=50,
    )
    metrics = backtest.run()

    print("Backtest completed")
    print("-" * 40)
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"{key:>20}: {value:.4f}")
        else:
            print(f"{key:>20}: {value}")


if __name__ == "__main__":
    main()
