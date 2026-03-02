"""CLI entrypoint for running backtest or real-time session simulation."""

from __future__ import annotations

import argparse
from pathlib import Path

from backtest import Backtest
from realtime import (
    MomentumRealtimeStrategy,
    MovingAverageCrossRealtimeStrategy,
    RealTimeBacktestEngine,
)


def run_historical_backtest() -> None:
    """Run sample historical backtest and print summary metrics."""
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


def run_realtime_session(symbols: list[str], poll_seconds: int, output_dir: str) -> None:
    """Run market-hours polling session and print report path."""
    strategies = [
        MovingAverageCrossRealtimeStrategy(short_window=20, long_window=50),
        MomentumRealtimeStrategy(lookback=30),
    ]
    engine = RealTimeBacktestEngine(
        symbols=symbols,
        strategies=strategies,
        poll_seconds=poll_seconds,
        output_dir=output_dir,
    )
    report_path = engine.run_session()
    print(f"Real-time session finished. Report: {report_path}")


def build_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI modes."""
    parser = argparse.ArgumentParser(description="Event-driven backtesting engine")
    parser.add_argument(
        "--mode",
        choices=["historical", "realtime"],
        default="historical",
        help="Execution mode: historical backtest or real-time session",
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["AAPL"],
        help="Symbols to track in real-time mode",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=60,
        help="Polling interval for real-time mode",
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Directory for end-of-day real-time reports",
    )
    return parser


def main() -> None:
    """Dispatch CLI mode."""
    args = build_parser().parse_args()

    if args.mode == "historical":
        run_historical_backtest()
    else:
        run_realtime_session(args.symbols, args.poll_seconds, args.output_dir)


if __name__ == "__main__":
    main()
