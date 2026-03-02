# Implementation Guide

## Step-by-Step Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Ensure `data/AAPL.csv` exists (included).
3. Run:
   ```bash
   python src/main.py
   ```

## Module-by-Module Explanation

- `event.py`: immutable event objects that travel through the engine.
- `event_queue.py`: FIFO queue built on `collections.deque`.
- `data_handler.py`: reads historical CSV and emits one `MarketEvent` per bar.
- `strategy.py`: abstract strategy interface + moving-average crossover implementation.
- `portfolio.py`: converts signals to orders and updates account state after fills.
- `execution.py`: simulates fills with fixed cost + slippage assumptions.
- `performance.py`: transforms holdings snapshots into metrics.
- `backtest.py`: central loop coordinating all modules.
- `main.py`: runnable entrypoint.

## Event Loop Explanation

For each bar:
1. Data handler yields `MarketEvent`
2. Strategy may yield `SignalEvent`
3. Portfolio may yield `OrderEvent`
4. Execution converts order to `FillEvent`
5. Portfolio updates positions/cash and snapshots holdings

This sequence enforces realistic ordering and avoids lookahead bias from direct vectorized shortcuts.

## Financial Metric Formulas

- **Total Return**: `equity_end / equity_start - 1`
- **Annualized Return**: `(1 + total_return)^(periods_per_year / n_periods) - 1`
- **Volatility**: `std(returns) * sqrt(periods_per_year)`
- **Sharpe Ratio** (rf=0): `mean(returns) / std(returns) * sqrt(periods_per_year)`
- **Max Drawdown**: `max(1 - equity / rolling_max_equity)`

## Extension Ideas

- Add new strategy classes implementing `Strategy.calculate_signals`
- Introduce multi-symbol position sizing policies
- Add benchmark comparison and alpha/beta metrics
- Persist trade logs to database for auditability
