# event-driven-backtesting-engine

A production-quality, modular Python backtesting project implementing a true event-driven trading workflow.

## Overview

This project simulates professional quant architecture where each module communicates through events, not direct tight coupling.

Event flow:

1. `HistoricCSVDataHandler` streams bars and emits `MarketEvent`
2. `Strategy` consumes market events and emits `SignalEvent`
3. `Portfolio` converts signals into `OrderEvent`
4. `SimulatedExecutionHandler` converts orders to `FillEvent`
5. `Portfolio` updates positions, cash, and holdings from fills
6. `performance.py` computes return/risk metrics

## System Diagram (Conceptual)

`CSV Data -> MarketEvent -> Strategy -> SignalEvent -> Portfolio -> OrderEvent -> Execution -> FillEvent -> Portfolio -> Performance`

## Installation

```bash
pip install -r requirements.txt
```

## How to Run

```bash
python src/main.py
```

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

## Future Extensions

- Multi-asset portfolio constraints and risk budgeting
- Advanced execution models (partial fills, latency, limit orders)
- Transaction cost models by venue and liquidity regime
- Walk-forward optimization and parameter sweeps
- Tearsheet report generation with richer analytics
