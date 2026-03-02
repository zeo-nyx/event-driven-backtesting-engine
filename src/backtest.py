"""Backtest engine orchestrating event-driven modules."""

from __future__ import annotations

from pathlib import Path

from data_handler import HistoricCSVDataHandler
from event import FillEvent, MarketEvent, OrderEvent, SignalEvent
from event_queue import EventQueue
from execution import SimulatedExecutionHandler
from performance import calculate_performance_metrics, create_equity_curve
from portfolio import Portfolio
from strategy import MovingAverageCrossStrategy, Strategy


class Backtest:
    """Coordinates the full event-driven simulation."""

    def __init__(
        self,
        csv_dir: str | Path,
        symbol_list: list[str],
        initial_capital: float = 100000.0,
        short_window: int = 20,
        long_window: int = 50,
    ) -> None:
        self.events = EventQueue()
        self.data_handler = HistoricCSVDataHandler(csv_dir, symbol_list)
        self.strategy: Strategy = MovingAverageCrossStrategy(
            self.data_handler, symbol_list, short_window, long_window
        )
        self.portfolio = Portfolio(self.data_handler, symbol_list, initial_capital=initial_capital)
        self.execution_handler = SimulatedExecutionHandler(self.data_handler)
        self.signals = 0
        self.orders = 0
        self.fills = 0

    def _process_event(self, event: MarketEvent | SignalEvent | OrderEvent | FillEvent) -> None:
        if event.type == "MARKET":
            market_event = event
            self.portfolio.update_timeindex(market_event.timestamp)
            for signal in self.strategy.calculate_signals(market_event):
                self.events.put(signal)

        elif event.type == "SIGNAL":
            self.signals += 1
            order = self.portfolio.update_signal(event)
            if order is not None:
                self.events.put(order)

        elif event.type == "ORDER":
            self.orders += 1
            self.events.put(self.execution_handler.execute_order(event))

        elif event.type == "FILL":
            self.fills += 1
            self.portfolio.update_fill(event)

    def run(self) -> dict[str, float]:
        """Run simulation loop until historical data is exhausted."""
        while self.data_handler.continue_backtest:
            market_events = self.data_handler.update_bars()
            for market_event in market_events:
                self.events.put(market_event)

            while not self.events.is_empty():
                next_event = self.events.get()
                if next_event is None:
                    break
                self._process_event(next_event)

        equity_curve = create_equity_curve(self.portfolio.all_holdings)
        metrics = calculate_performance_metrics(equity_curve)
        metrics.update({"signals": self.signals, "orders": self.orders, "fills": self.fills})
        return metrics
