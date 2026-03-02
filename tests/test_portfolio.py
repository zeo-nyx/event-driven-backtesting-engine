"""Unit tests for portfolio accounting logic."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "src"))

from data_handler import HistoricCSVDataHandler
from event import FillEvent, SignalEvent
from portfolio import Portfolio


def test_portfolio_signal_to_order_and_fill_updates_cash_and_position() -> None:
    bars = HistoricCSVDataHandler(ROOT / "data", ["AAPL"])
    bars.update_bars()

    portfolio = Portfolio(bars, ["AAPL"], initial_capital=100000.0, base_order_size=10)

    signal = SignalEvent(symbol="AAPL", timestamp=datetime.utcnow(), signal_type="LONG")
    order = portfolio.update_signal(signal)

    assert order is not None
    assert order.quantity == 10
    assert order.direction == "BUY"

    fill = FillEvent(
        symbol="AAPL",
        timestamp=signal.timestamp,
        quantity=10,
        direction="BUY",
        fill_cost=100.0,
        commission=1.0,
        slippage=0.5,
    )
    portfolio.update_fill(fill)

    assert portfolio.current_positions["AAPL"] == 10
    assert portfolio.current_holdings["cash"] == 100000.0 - (100.0 * 10 + 1.0 + 0.5)
