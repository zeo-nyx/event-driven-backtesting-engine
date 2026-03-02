# event-driven-backtesting-engine

A modular, production-style **event-driven backtesting engine** in Python.  
It demonstrates how professional quant systems separate market data ingestion, signal generation, portfolio construction, execution simulation, and performance analytics via explicit event flow.

---

## Table of Contents

- [Why Event-Driven Backtesting](#why-event-driven-backtesting)
- [Core Architecture](#core-architecture)
- [System Event Flow](#system-event-flow)
- [Project Structure](#project-structure)
- [Module Responsibilities](#module-responsibilities)
- [Data Format](#data-format)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [Running Tests](#running-tests)
- [Example Output](#example-output)
- [Performance Metrics](#performance-metrics)
- [Design Decisions](#design-decisions)
- [Extension Guide](#extension-guide)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)

---

## Why Event-Driven Backtesting

Many beginner backtests use purely vectorized logic, which is useful for fast research but can hide critical sequencing behavior:

- When signals are generated vs. when orders are executed
- How transaction costs and slippage impact realized PnL
- How portfolio state evolves over time (cash, holdings, equity)

This engine models a realistic lifecycle with explicit events:

`MarketEvent -> SignalEvent -> OrderEvent -> FillEvent`

That lifecycle is easier to reason about, debug, test, and eventually adapt for paper/live trading workflows.

---

## Core Architecture

The system follows clean component boundaries:

1. **Data Handler**  
   Streams historical OHLCV bars one row at a time.
2. **Strategy**  
   Reads market events and emits trading signals.
3. **Portfolio**  
   Converts signals into orders and updates account state on fills.
4. **Execution Handler**  
   Simulates fills using slippage + transaction costs.
5. **Performance**  
   Builds an equity curve and computes risk/return metrics.
6. **Backtest Engine**  
   Owns the event loop and orchestrates interactions.

---

## System Event Flow

```text
CSV Data
   |
   v
MarketEvent  -->  Strategy  -->  SignalEvent  -->  Portfolio  -->  OrderEvent
                                                                  |
                                                                  v
                                                           ExecutionHandler
                                                                  |
                                                                  v
                                                             FillEvent
                                                                  |
                                                                  v
                                                              Portfolio
                                                                  |
                                                                  v
                                                              Performance
```

Event transport is done through a FIFO queue implemented with `collections.deque`.

---

## Project Structure

```text
event-driven-backtesting-engine/
├── data/
│   └── AAPL.csv
├── src/
│   ├── __init__.py
│   ├── event.py
│   ├── event_queue.py
│   ├── data_handler.py
│   ├── strategy.py
│   ├── portfolio.py
│   ├── execution.py
│   ├── performance.py
│   ├── backtest.py
│   └── main.py
├── tests/
│   ├── test_portfolio.py
│   └── test_strategy.py
├── requirements.txt
├── README.md
├── prd.md
├── techstack.md
├── implementation.md
└── .gitignore
```

---

## Module Responsibilities

### `src/event.py`
Defines immutable event models:
- `MarketEvent`
- `SignalEvent`
- `OrderEvent`
- `FillEvent`

### `src/event_queue.py`
Thin queue abstraction over `deque` to push/pop events in arrival order.

### `src/data_handler.py`
Loads CSV bars with pandas, validates expected columns, and emits market events bar-by-bar.

### `src/strategy.py`
Contains:
- `Strategy` abstract interface
- `MovingAverageCrossStrategy` concrete implementation

The default strategy emits:
- `LONG` when short SMA crosses above long SMA
- `EXIT` when short SMA crosses below long SMA

### `src/portfolio.py`
Tracks:
- Symbol positions
- Symbol market values
- Cash
- Accumulated costs
- Total equity

Handles:
- `SignalEvent -> OrderEvent` conversion
- Fill-based portfolio updates

### `src/execution.py`
Simulates order execution with:
- Fixed commission
- Percentage slippage

### `src/performance.py`
Builds equity curve and computes:
- Total return
- Annualized return
- Volatility
- Sharpe ratio
- Max drawdown

### `src/backtest.py`
Owns the master loop and event dispatch until market data is exhausted.

### `src/main.py`
Runnable CLI entrypoint for a full end-to-end backtest.

---

## Data Format

CSV files are expected in `data/` with one file per symbol, e.g. `AAPL.csv`.

Required columns:
- `datetime`
- `open`
- `high`
- `low`
- `close`
- `volume`

Rows should be sorted by time (or sortable by `datetime`).

---

## Installation

```bash
pip install -r requirements.txt
```

Dependencies:
- `pandas`
- `numpy`
- `matplotlib`

---

## How to Run

```bash
python src/main.py
```

The script:
1. Loads `data/AAPL.csv`
2. Runs the moving-average strategy through the event engine
3. Prints summary performance metrics

---


## Real-Time Session Mode

The CLI now supports a **real-time market-hours session mode** that continuously polls intraday data, evaluates multiple strategies, and generates an end-of-day comparison report.

### Included Real-Time Strategies

- `MA_CROSS_20_50`: short/long moving-average crossover
- `MOMENTUM_30`: breakout momentum over recent lookback window

### How It Works

During US market hours (9:30 AM to 4:00 PM ET):

1. Fetch intraday 1-minute bars from Yahoo Finance
2. Process unseen bars through each strategy
3. Simulate paper trades with slippage and commission
4. Track per-strategy cash, positions, and realized PnL
5. Save end-of-day report in `reports/report_YYYYMMDD.md`

### Run Real-Time Mode

```bash
python src/main.py --mode realtime --symbols AAPL MSFT --poll-seconds 60 --output-dir reports
```

> Note: real-time mode waits for market open and runs until market close.

---

## Running Tests

```bash
pytest -q
```

Included tests cover:
- Strategy signal generation behavior
- Portfolio order/fill accounting behavior

---

## Example Output

```text
Backtest completed
----------------------------------------
        total_return: 0.1218
   annualized_return: 0.0940
          volatility: 0.1182
        sharpe_ratio: 0.8120
        max_drawdown: 0.0651
             signals: 7
              orders: 7
               fills: 7
```

(Exact values vary with data and parameters.)

---

## Performance Metrics

- **Total Return**: Net portfolio growth over the full test period.
- **Annualized Return**: Return scaled to yearly frequency.
- **Volatility**: Standard deviation of periodic returns, annualized.
- **Sharpe Ratio**: Risk-adjusted return (`mean/std`, annualized, rf=0).
- **Max Drawdown**: Largest peak-to-trough equity decline.

---

## Design Decisions

- **Event-driven queue** instead of direct method chaining to keep components decoupled.
- **Pluggable strategy interface** via an abstract base class.
- **No global mutable state** to improve reproducibility and testability.
- **Simple execution model** (fixed fee + slippage) as a realistic baseline.

---

## Extension Guide

Common next steps:

1. Add strategies by implementing `Strategy.calculate_signals`.
2. Support multiple symbols and dynamic position sizing.
3. Add risk overlays (max leverage, exposure limits, stop loss).
4. Replace immediate-fill execution with limit/partial fill simulation.
5. Add plotting/reporting for equity and drawdowns.
6. Add parameter sweeps and walk-forward validation.

---

## Troubleshooting

### `ModuleNotFoundError` for `pandas`/`numpy`
Install dependencies:

```bash
pip install -r requirements.txt
```

### Tests fail during import
Ensure your environment points to project root and dependencies are installed.

### `python src/main.py` cannot find data
Confirm `data/AAPL.csv` exists and includes required OHLCV columns.

---

## Future Enhancements

- Real-time websocket data adapter
- Paper-trading/live-trading bridge
- Advanced transaction cost and market impact models
- Benchmark-relative analytics (alpha/beta/information ratio)
- Portfolio optimization and risk-parity allocation options
