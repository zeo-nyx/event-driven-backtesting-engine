"""Execution simulation with fixed fees and slippage."""

from __future__ import annotations

from data_handler import HistoricCSVDataHandler
from event import FillEvent, OrderEvent


class SimulatedExecutionHandler:
    """Converts order events into realistic fill events."""

    def __init__(self, bars: HistoricCSVDataHandler, fixed_cost: float = 1.0, slippage_pct: float = 0.001) -> None:
        self.bars = bars
        self.fixed_cost = fixed_cost
        self.slippage_pct = slippage_pct

    def execute_order(self, order: OrderEvent) -> FillEvent:
        """Immediate-fill model using latest close plus/minus slippage."""
        latest_price = self.bars.get_latest_bar_value(order.symbol, "close")

        if order.direction.upper() == "BUY":
            fill_price = latest_price * (1.0 + self.slippage_pct)
        else:
            fill_price = latest_price * (1.0 - self.slippage_pct)

        slippage_cost = latest_price * self.slippage_pct * order.quantity

        return FillEvent(
            symbol=order.symbol,
            timestamp=order.timestamp,
            quantity=order.quantity,
            direction=order.direction,
            fill_cost=fill_price,
            commission=self.fixed_cost,
            slippage=slippage_cost,
        )
