"""Strategy abstractions and concrete implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod

from data_handler import HistoricCSVDataHandler
from event import MarketEvent, SignalEvent


class Strategy(ABC):
    """Abstract strategy interface for pluggable signal generation."""

    @abstractmethod
    def calculate_signals(self, event: MarketEvent) -> list[SignalEvent]:
        """Process market events and emit 0..n signal events."""


class MovingAverageCrossStrategy(Strategy):
    """Classic short/long moving average crossover strategy."""

    def __init__(
        self,
        bars: HistoricCSVDataHandler,
        symbol_list: list[str],
        short_window: int = 20,
        long_window: int = 50,
    ) -> None:
        if short_window >= long_window:
            raise ValueError("short_window must be less than long_window")
        self.bars = bars
        self.symbol_list = symbol_list
        self.short_window = short_window
        self.long_window = long_window
        self.bought: dict[str, str] = {s: "OUT" for s in symbol_list}

    def calculate_signals(self, event: MarketEvent) -> list[SignalEvent]:
        signals: list[SignalEvent] = []
        if event.type != "MARKET":
            return signals

        symbol = event.symbol
        short_sma = self.bars.get_latest_bars_values(symbol, "close", self.short_window).mean()
        long_sma = self.bars.get_latest_bars_values(symbol, "close", self.long_window).mean()

        if short_sma != short_sma or long_sma != long_sma:  # NaN check
            return signals

        if short_sma > long_sma and self.bought[symbol] == "OUT":
            signals.append(SignalEvent(symbol, event.timestamp, "LONG"))
            self.bought[symbol] = "LONG"
        elif short_sma < long_sma and self.bought[symbol] == "LONG":
            signals.append(SignalEvent(symbol, event.timestamp, "EXIT"))
            self.bought[symbol] = "OUT"

        return signals
