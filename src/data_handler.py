"""Historical CSV data ingestion and market event generation."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterator

import pandas as pd

from event import MarketEvent


class HistoricCSVDataHandler:
    """Streams bars one-by-one from a CSV into MarketEvent objects."""

    def __init__(self, csv_dir: str | Path, symbol_list: list[str]) -> None:
        self.csv_dir = Path(csv_dir)
        self.symbol_list = symbol_list
        self.continue_backtest = True
        self._symbol_data: Dict[str, pd.DataFrame] = {}
        self._bar_generators: Dict[str, Iterator[pd.Series]] = {}
        self.latest_symbol_data: Dict[str, list[pd.Series]] = {s: [] for s in symbol_list}
        self._open_convert_csv_files()

    def _open_convert_csv_files(self) -> None:
        for symbol in self.symbol_list:
            csv_path = self.csv_dir / f"{symbol}.csv"
            data = pd.read_csv(csv_path, parse_dates=["datetime"]).sort_values("datetime")
            required = {"datetime", "open", "high", "low", "close", "volume"}
            missing = required - set(data.columns)
            if missing:
                raise ValueError(f"Missing required columns in {csv_path}: {missing}")
            data = data.set_index("datetime")
            self._symbol_data[symbol] = data
            self._bar_generators[symbol] = data.iterrows()

    def get_latest_bar_value(self, symbol: str, val_type: str) -> float:
        """Return latest known value for a symbol field (e.g. close)."""
        bars = self.latest_symbol_data[symbol]
        if not bars:
            raise ValueError(f"No bars available for symbol {symbol}")
        return float(bars[-1][val_type])

    def get_latest_bars_values(self, symbol: str, val_type: str, n: int = 1) -> pd.Series:
        """Return last n values from streamed bars for indicator computation."""
        bars = self.latest_symbol_data[symbol]
        if not bars:
            return pd.Series(dtype=float)
        subset = bars[-n:]
        return pd.Series([float(b[val_type]) for b in subset])

    def update_bars(self) -> list[MarketEvent]:
        """Advance all symbols by one bar and produce corresponding MarketEvents."""
        events: list[MarketEvent] = []
        for symbol in self.symbol_list:
            try:
                timestamp, bar = next(self._bar_generators[symbol])
            except StopIteration:
                self.continue_backtest = False
                return events

            self.latest_symbol_data[symbol].append(bar)
            events.append(
                MarketEvent(
                    symbol=symbol,
                    timestamp=timestamp.to_pydatetime(),
                    close=float(bar["close"]),
                    volume=float(bar["volume"]),
                )
            )
        return events
