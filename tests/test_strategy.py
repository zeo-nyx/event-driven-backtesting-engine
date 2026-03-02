"""Unit tests for strategy behavior."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "src"))

from data_handler import HistoricCSVDataHandler
from event import MarketEvent
from strategy import MovingAverageCrossStrategy


def test_moving_average_strategy_emits_signal_after_enough_data() -> None:
    bars = HistoricCSVDataHandler(ROOT / "data", ["AAPL"])
    strategy = MovingAverageCrossStrategy(bars, ["AAPL"], short_window=5, long_window=20)

    collected = []
    while bars.continue_backtest and len(collected) < 1:
        events = bars.update_bars()
        for evt in events:
            assert isinstance(evt, MarketEvent)
            collected.extend(strategy.calculate_signals(evt))

    assert len(collected) >= 1
    assert collected[0].signal_type in {"LONG", "EXIT"}
    assert isinstance(collected[0].timestamp, datetime)
