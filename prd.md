# Product Requirements Document (PRD)

## Overview

`event-driven-backtesting-engine` is a modular simulation framework for testing systematic strategies with realistic order/fill/accounting behavior.

## Problem Statement

Many beginner backtests are vectorized only, which hides sequencing effects and realistic execution costs. Professional systems require event-driven sequencing to reproduce real trading lifecycles.

## Goals

- Implement a complete event-driven lifecycle for strategy testing
- Keep modules pluggable and testable
- Provide institutional-style performance metrics
- Maintain readability for students and interns

## System Architecture

- **Data Handler**: historical data streaming one bar at a time
- **Event Queue**: `collections.deque` for FIFO event dispatch
- **Strategy**: market-event consumer producing trading signals
- **Portfolio**: order generation + account state management
- **Execution**: fill simulation with commissions/slippage
- **Performance**: return and risk analytics
- **Backtest Engine**: orchestrates event loop until data exhausted

## Functional Requirements

1. Support `MarketEvent`, `SignalEvent`, `OrderEvent`, `FillEvent`
2. Load CSV OHLCV data
3. Implement moving-average crossover strategy
4. Track positions, cash, commission, total equity
5. Simulate transaction fees and slippage
6. Compute total return, annualized return, volatility, Sharpe, max drawdown

## Non-Functional Requirements

- OOP and modular design
- Type hints and docstrings
- PEP8-compliant code
- No global mutable state
- Runnable from CLI
- Basic unit tests

## Success Criteria

- Running `python src/main.py` prints consistent metrics
- Unit tests validate strategy and portfolio logic
- Architecture can accept new strategy classes without engine changes

## Future Scope

- Live-paper trading adapter
- Risk overlays (exposure limits, stop-loss logic)
- Parameter optimization and cross-validation
- Intraday data and event-time modeling
