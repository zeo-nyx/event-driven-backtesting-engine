"""Unit tests for real-time strategy and paper-trade behavior."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "src"))

from realtime import (  # noqa: E402
    MovingAverageCrossRealtimeStrategy,
    RealtimeBar,
    StrategySessionState,
)


def test_realtime_ma_strategy_emits_long_signal() -> None:
    strategy = MovingAverageCrossRealtimeStrategy(short_window=3, long_window=5)
    bars = [
        RealtimeBar("AAPL", datetime(2024, 1, 1, 10, i), close=price, volume=1000)
        for i, price in enumerate([100.0, 100.2, 100.4, 100.6, 101.0, 101.5])
    ]

    signals = [strategy.on_bar(bar) for bar in bars]
    assert "LONG" in signals


def test_strategy_session_state_mark_to_market() -> None:
    state = StrategySessionState(strategy_name="TEST", cash=99000.0, position_qty=100)
    equity = state.mark_to_market(last_price=12.5)
    assert equity == 100250.0
