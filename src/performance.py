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
    """Compute core professional trading performance statistics."""
    returns = equity_curve["returns"]
    total_return = equity_curve["equity_curve"].iloc[-1] - 1.0

    n_periods = len(returns)
    if n_periods == 0:
        raise ValueError("Equity curve contains no observations")

    annualized_return = (1.0 + total_return) ** (periods_per_year / max(n_periods, 1)) - 1.0
    volatility = returns.std(ddof=0) * np.sqrt(periods_per_year)
    sharpe = (returns.mean() / returns.std(ddof=0) * np.sqrt(periods_per_year)) if returns.std(ddof=0) > 0 else 0.0

    rolling_max = equity_curve["equity_curve"].cummax()
    drawdown = equity_curve["equity_curve"] / rolling_max - 1.0
    max_drawdown = abs(drawdown.min())

    return {
        "total_return": float(total_return),
        "annualized_return": float(annualized_return),
        "volatility": float(volatility),
        "sharpe_ratio": float(sharpe),
        "max_drawdown": float(max_drawdown),
    }
