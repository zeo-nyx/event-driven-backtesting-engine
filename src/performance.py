"""Performance analytics for backtest results."""

from __future__ import annotations

import numpy as np
import pandas as pd


def create_equity_curve(holdings: list[dict[str, float | object]]) -> pd.DataFrame:
    """Convert holdings snapshots into a returns/equity curve DataFrame."""
    curve = pd.DataFrame(holdings)
    curve = curve.set_index("datetime")
    curve["returns"] = curve["total"].pct_change().fillna(0.0)
    curve["equity_curve"] = (1.0 + curve["returns"]).cumprod()
    return curve


def calculate_performance_metrics(equity_curve: pd.DataFrame, periods_per_year: int = 252) -> dict[str, float]:
    """Compute core professional trading performance statistics.

    Optimizations:
    - Single std computation reused for volatility and Sharpe
    - Works on numpy arrays for less pandas overhead in hot calculations
    """
    returns_series = equity_curve["returns"]
    returns = returns_series.to_numpy(dtype=float)

    if returns.size == 0:
        raise ValueError("Equity curve contains no observations")

    total_return = float(equity_curve["equity_curve"].iloc[-1] - 1.0)
    annualized_return = (1.0 + total_return) ** (periods_per_year / returns.size) - 1.0

    ret_std = float(returns.std())
    ret_mean = float(returns.mean())
    volatility = ret_std * np.sqrt(periods_per_year)
    sharpe = (ret_mean / ret_std * np.sqrt(periods_per_year)) if ret_std > 0 else 0.0

    rolling_max = equity_curve["equity_curve"].cummax()
    drawdown = equity_curve["equity_curve"] / rolling_max - 1.0
    max_drawdown = float(abs(drawdown.min()))

    return {
        "total_return": total_return,
        "annualized_return": float(annualized_return),
        "volatility": float(volatility),
        "sharpe_ratio": float(sharpe),
        "max_drawdown": max_drawdown,
    }
