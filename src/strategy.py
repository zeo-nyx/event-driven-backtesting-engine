"""Strategy abstractions and concrete implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from math import isnan

from data_handler import HistoricCSVDataHandler
from event import MarketEvent, SignalEvent


class Strategy(ABC):
    """Abstract strategy interface for pluggable signal generation."""

    @abstractmethod
    def calculate_signals(self, event: MarketEvent) -> list[SignalEvent]:
        """Process market events and emit 0..n signal events."""


class MovingAverageCrossStrategy(Strategy):
    """Classic short/long moving average crossover strategy.

    Optimized implementation:
    - Maintains rolling windows and running sums per symbol
    - Avoids rebuilding pandas series and recomputing means each bar
    """

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

        self._short_prices: dict[str, deque[float]] = {s: deque(maxlen=short_window) for s in symbol_list}
        self._long_prices: dict[str, deque[float]] = {s: deque(maxlen=long_window) for s in symbol_list}
        self._short_sum: dict[str, float] = {s: 0.0 for s in symbol_list}
        self._long_sum: dict[str, float] = {s: 0.0 for s in symbol_list}

    def _push_price(self, symbol: str, price: float) -> None:
        short_q = self._short_prices[symbol]
        long_q = self._long_prices[symbol]

        if len(short_q) == self.short_window:
            self._short_sum[symbol] -= short_q[0]
        if len(long_q) == self.long_window:
            self._long_sum[symbol] -= long_q[0]

        short_q.append(price)
        long_q.append(price)

        self._short_sum[symbol] += price
        self._long_sum[symbol] += price

    def calculate_signals(self, event: MarketEvent) -> list[SignalEvent]:
        signals: list[SignalEvent] = []
        if event.type != "MARKET":
            return signals

        symbol = event.symbol
        self._push_price(symbol, event.close)

        if len(self._long_prices[symbol]) < self.long_window:
            return signals

        short_sma = self._short_sum[symbol] / self.short_window
        long_sma = self._long_sum[symbol] / self.long_window

        if isnan(short_sma) or isnan(long_sma):
            return signals

        if short_sma > long_sma and self.bought[symbol] == "OUT":
            signals.append(SignalEvent(symbol, event.timestamp, "LONG"))
            self.bought[symbol] = "LONG"
        elif short_sma < long_sma and self.bought[symbol] == "LONG":
            signals.append(SignalEvent(symbol, event.timestamp, "EXIT"))
            self.bought[symbol] = "OUT"

        return signals
