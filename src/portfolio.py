"""Portfolio accounting, risk state, and order generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from data_handler import HistoricCSVDataHandler
from event import FillEvent, OrderEvent, SignalEvent


@dataclass
class PortfolioSnapshot:
    """Tracks account state at each bar for performance analysis."""

    datetime: datetime
    cash: float
    commission: float
    total: float


class Portfolio:
    """Portfolio converts signals into orders and tracks PnL over time."""

    def __init__(
        self,
        bars: HistoricCSVDataHandler,
        symbol_list: list[str],
        initial_capital: float = 100000.0,
        base_order_size: int = 100,
    ) -> None:
        self.bars = bars
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.base_order_size = base_order_size

        self.current_positions: dict[str, int] = {s: 0 for s in symbol_list}
        self.current_holdings: dict[str, float] = {
            s: 0.0 for s in symbol_list
        }
        self.current_holdings["cash"] = initial_capital
        self.current_holdings["commission"] = 0.0
        self.current_holdings["total"] = initial_capital

        self.all_positions: list[dict[str, int | datetime]] = []
        self.all_holdings: list[dict[str, float | datetime]] = []

    def update_timeindex(self, timestamp: datetime) -> None:
        """Record portfolio valuation at latest market prices."""
        position_snapshot: dict[str, int | datetime] = {"datetime": timestamp}
        position_snapshot.update(self.current_positions)
        self.all_positions.append(position_snapshot)

        holdings_snapshot: dict[str, float | datetime] = {
            "datetime": timestamp,
            "cash": self.current_holdings["cash"],
            "commission": self.current_holdings["commission"],
        }

        total = self.current_holdings["cash"]
        for symbol in self.symbol_list:
            market_value = self.current_positions[symbol] * self.bars.get_latest_bar_value(symbol, "close")
            holdings_snapshot[symbol] = market_value
            total += market_value

        holdings_snapshot["total"] = total
        self.current_holdings["total"] = total
        self.all_holdings.append(holdings_snapshot)

    def generate_order(self, signal: SignalEvent) -> OrderEvent | None:
        """Transform a signal into a market order with simple sizing rules."""
        symbol = signal.symbol
        direction = signal.signal_type
        current_qty = self.current_positions[symbol]

        if direction == "LONG" and current_qty == 0:
            return OrderEvent(symbol, signal.timestamp, "MKT", self.base_order_size, "BUY")

        if direction == "EXIT" and current_qty > 0:
            return OrderEvent(symbol, signal.timestamp, "MKT", abs(current_qty), "SELL")

        return None

    def update_signal(self, signal: SignalEvent) -> OrderEvent | None:
        """Entry point called by the backtest loop when a signal arrives."""
        return self.generate_order(signal)

    def update_fill(self, fill: FillEvent) -> None:
        """Update positions and holdings after an order fill.

        Financial logic:
        - Buy fills decrease cash; sell fills increase cash.
        - Commission and slippage are treated as explicit costs.
        """
        symbol = fill.symbol
        fill_dir = 1 if fill.direction.upper() == "BUY" else -1

        self.current_positions[symbol] += fill_dir * fill.quantity

        gross_cost = fill.fill_cost * fill.quantity * fill_dir
        total_cost = gross_cost + fill.commission + fill.slippage

        self.current_holdings[symbol] += gross_cost
        self.current_holdings["commission"] += fill.commission + fill.slippage
        self.current_holdings["cash"] -= total_cost
