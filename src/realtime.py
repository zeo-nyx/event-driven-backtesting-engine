"""Real-time session runner for market-hours strategy comparison.

This module provides a production-style intraday simulation loop that:
1) polls fresh market bars during US market hours,
2) evaluates multiple strategies on the same stream,
3) paper-trades each strategy independently, and
4) emits an end-of-day comparative report.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Protocol
from zoneinfo import ZoneInfo
import json
import statistics
import time as time_module
import urllib.request
from urllib.error import URLError, HTTPError


EASTERN_TZ = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class RealtimeBar:
    """Represents one intraday OHLCV snapshot for a symbol."""

    symbol: str
    timestamp: datetime
    close: float
    volume: float


class IntradayDataFetcher(Protocol):
    """Protocol for providers that return intraday bars for a symbol."""

    def fetch_intraday_bars(self, symbol: str) -> list[RealtimeBar]:
        """Return all intraday bars available for the current session."""


class YahooFinanceIntradayFetcher:
    """Fetches 1-minute bars from Yahoo Finance chart API."""

    base_url = "https://query1.finance.yahoo.com/v8/finance/chart"

    def fetch_intraday_bars(self, symbol: str) -> list[RealtimeBar]:
        url = f"{self.base_url}/{symbol}?interval=1m&range=1d"
        req = urllib.request.Request(url, headers={"User-Agent": "event-driven-backtesting-engine/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (URLError, HTTPError, TimeoutError):
            return []

        result = payload["chart"]["result"][0]
        timestamps = result.get("timestamp", [])
        quote = result["indicators"]["quote"][0]
        closes = quote.get("close", [])
        volumes = quote.get("volume", [])

        bars: list[RealtimeBar] = []
        for ts, close, volume in zip(timestamps, closes, volumes):
            if close is None:
                continue
            dt = datetime.fromtimestamp(ts, tz=EASTERN_TZ)
            bars.append(
                RealtimeBar(
                    symbol=symbol,
                    timestamp=dt,
                    close=float(close),
                    volume=float(volume or 0),
                )
            )
        return bars


class RealtimeStrategy(Protocol):
    """Interface for strategies evaluated in the real-time session."""

    name: str

    def on_bar(self, bar: RealtimeBar) -> str | None:
        """Consume a new bar and optionally emit LONG or EXIT signal."""


class MovingAverageCrossRealtimeStrategy:
    """Realtime short/long moving-average crossover strategy."""

    def __init__(self, short_window: int = 20, long_window: int = 50) -> None:
        if short_window >= long_window:
            raise ValueError("short_window must be less than long_window")
        self.name = f"MA_CROSS_{short_window}_{long_window}"
        self.short_window = short_window
        self.long_window = long_window
        self._prices: list[float] = []
        self._in_position = False

    def on_bar(self, bar: RealtimeBar) -> str | None:
        self._prices.append(bar.close)
        if len(self._prices) < self.long_window:
            return None

        short_avg = statistics.fmean(self._prices[-self.short_window :])
        long_avg = statistics.fmean(self._prices[-self.long_window :])

        if short_avg > long_avg and not self._in_position:
            self._in_position = True
            return "LONG"
        if short_avg < long_avg and self._in_position:
            self._in_position = False
            return "EXIT"
        return None


class MomentumRealtimeStrategy:
    """Simple breakout momentum strategy based on recent lookback highs/lows."""

    def __init__(self, lookback: int = 30) -> None:
        self.name = f"MOMENTUM_{lookback}"
        self.lookback = lookback
        self._prices: list[float] = []
        self._in_position = False

    def on_bar(self, bar: RealtimeBar) -> str | None:
        self._prices.append(bar.close)
        if len(self._prices) <= self.lookback:
            return None

        window = self._prices[-self.lookback - 1 : -1]
        if not window:
            return None

        if bar.close > max(window) and not self._in_position:
            self._in_position = True
            return "LONG"
        if bar.close < min(window) and self._in_position:
            self._in_position = False
            return "EXIT"
        return None


@dataclass
class StrategySessionState:
    """Paper-trading state for one strategy during current session."""

    strategy_name: str
    cash: float
    position_qty: int = 0
    entry_price: float = 0.0
    trades: int = 0
    realized_pnl: float = 0.0

    def mark_to_market(self, last_price: float) -> float:
        """Compute total equity from cash + open position at latest price."""
        return self.cash + self.position_qty * last_price


class RealTimeBacktestEngine:
    """Runs intraday polling and strategy comparison during market hours."""

    def __init__(
        self,
        symbols: list[str],
        strategies: list[RealtimeStrategy],
        fetcher: IntradayDataFetcher | None = None,
        initial_capital: float = 100000.0,
        order_size: int = 100,
        commission: float = 1.0,
        slippage_pct: float = 0.001,
        poll_seconds: int = 60,
        output_dir: str | Path = "reports",
    ) -> None:
        self.symbols = symbols
        self.strategies = strategies
        self.fetcher = fetcher or YahooFinanceIntradayFetcher()
        self.order_size = order_size
        self.commission = commission
        self.slippage_pct = slippage_pct
        self.poll_seconds = poll_seconds
        self.output_dir = Path(output_dir)
        self.last_seen_timestamp: dict[str, datetime | None] = {s: None for s in symbols}
        self.states: dict[str, StrategySessionState] = {
            s.name: StrategySessionState(strategy_name=s.name, cash=initial_capital) for s in strategies
        }

    @staticmethod
    def _market_window(now: datetime) -> tuple[datetime, datetime]:
        date_ = now.date()
        open_dt = datetime.combine(date_, time(9, 30), tzinfo=EASTERN_TZ)
        close_dt = datetime.combine(date_, time(16, 0), tzinfo=EASTERN_TZ)
        return open_dt, close_dt

    def _is_market_open(self, now: datetime) -> bool:
        open_dt, close_dt = self._market_window(now)
        return now.weekday() < 5 and open_dt <= now <= close_dt

    def _apply_signal(self, state: StrategySessionState, signal: str, price: float) -> None:
        slip = price * self.slippage_pct

        if signal == "LONG" and state.position_qty == 0:
            exec_price = price + slip
            cost = exec_price * self.order_size + self.commission
            if state.cash >= cost:
                state.cash -= cost
                state.position_qty = self.order_size
                state.entry_price = exec_price
                state.trades += 1

        if signal == "EXIT" and state.position_qty > 0:
            exec_price = price - slip
            proceeds = exec_price * state.position_qty - self.commission
            pnl = (exec_price - state.entry_price) * state.position_qty - self.commission
            state.cash += proceeds
            state.realized_pnl += pnl
            state.position_qty = 0
            state.entry_price = 0.0
            state.trades += 1

    def _format_report(self, final_prices: dict[str, float]) -> str:
        lines = [
            "# End-of-Day Strategy Comparison Report",
            "",
            f"Generated at: {datetime.now(tz=EASTERN_TZ).isoformat()}",
            "",
            "| Strategy | Trades | Realized PnL | Ending Equity | Open Position |",
            "|---|---:|---:|---:|---:|",
        ]

        last_price = next(iter(final_prices.values())) if final_prices else 0.0
        for state in self.states.values():
            equity = state.mark_to_market(last_price)
            lines.append(
                f"| {state.strategy_name} | {state.trades} | {state.realized_pnl:.2f} | {equity:.2f} | {state.position_qty} |"
            )
        return "\n".join(lines)

    def _persist_report(self, report_text: str) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename = datetime.now(tz=EASTERN_TZ).strftime("report_%Y%m%d.md")
        path = self.output_dir / filename
        path.write_text(report_text, encoding="utf-8")
        return path

    def run_session(self, max_wait_minutes: int = 120) -> Path:
        """Run a full market-hours session and return report file path."""
        wait_deadline = datetime.now(tz=EASTERN_TZ) + timedelta(minutes=max_wait_minutes)

        while True:
            now = datetime.now(tz=EASTERN_TZ)
            if self._is_market_open(now):
                break
            if now > wait_deadline:
                raise TimeoutError("Market did not open within configured wait window")
            time_module.sleep(min(self.poll_seconds, 30))

        final_prices: dict[str, float] = {}

        while True:
            now = datetime.now(tz=EASTERN_TZ)
            _, close_dt = self._market_window(now)
            if now > close_dt:
                break

            for symbol in self.symbols:
                bars = self.fetcher.fetch_intraday_bars(symbol)
                if not bars:
                    continue

                seen = self.last_seen_timestamp[symbol]
                if seen is None:
                    new_bars = bars
                else:
                    start = len(bars)
                    for idx in range(len(bars) - 1, -1, -1):
                        if bars[idx].timestamp <= seen:
                            start = idx + 1
                            break
                    new_bars = bars[start:]
                if not new_bars:
                    final_prices[symbol] = bars[-1].close
                    continue

                for bar in new_bars:
                    for strategy in self.strategies:
                        signal = strategy.on_bar(bar)
                        if signal is not None:
                            self._apply_signal(self.states[strategy.name], signal, bar.close)
                    final_prices[symbol] = bar.close

                self.last_seen_timestamp[symbol] = new_bars[-1].timestamp

            time_module.sleep(self.poll_seconds)

        report = self._format_report(final_prices)
        report_path = self._persist_report(report)
        return report_path
