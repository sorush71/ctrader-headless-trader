"""
Risk Management and Circuit Breaker System.
Ensures hard-coded financial safety, prevents account liquidation,
and protects against algorithmic infinite loops.
"""

import time
import logging
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, date

logger = logging.getLogger("RiskManager")


class RiskViolationError(Exception):
    """Raised when an order violates financial safety guardrails."""
    pass


@dataclass
class RiskConfig:
    max_lot_size: float = 0.50             # Absolute ceiling for a single order
    min_lot_size: float = 0.01             # Minimum allowed lot
    require_stop_loss: bool = True         # Disallow any order without Stop Loss
    max_open_positions: int = 3            # Max concurrent active trades
    max_daily_drawdown_pct: float = 4.0    # 4% max loss per day before kill-switch
    max_orders_per_minute: int = 5         # Anti-loop / flood protection


class RiskManager:
    """
    Independent Risk Supervisor that validates every trade before hitting the broker gateway.
    """

    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()
        self.kill_switch_active = False
        self.kill_switch_reason = ""
        self._order_timestamps: List[float] = []
        self._day_start_date: date = datetime.utcnow().date()
        self._initial_day_balance: Optional[float] = None
        logger.info(f"Initialized RiskManager with MaxLot={self.config.max_lot_size}, RequireSL={self.config.require_stop_loss}")

    def validate_order(self, order, account_summary, current_open_positions_count: int = 0):
        """
        Runs comprehensive security & financial checks on the proposed order.
        Raises RiskViolationError if any guardrail is breached.
        """
        # 1. Kill-Switch Check
        if self.kill_switch_active:
            raise RiskViolationError(f"EMERGENCY KILL-SWITCH ACTIVE: {self.kill_switch_reason}. Trading halted.")

        # 2. Daily Drawdown Evaluation
        self._check_daily_drawdown(account_summary)

        # 3. Lot Size Ceiling & Floor Check
        if order.volume > self.config.max_lot_size:
            raise RiskViolationError(
                f"ORDER REJECTED: Volume {order.volume} exceeds hard safety cap ({self.config.max_lot_size} lots)."
            )
        if order.volume < self.config.min_lot_size:
            raise RiskViolationError(
                f"ORDER REJECTED: Volume {order.volume} is below broker minimum ({self.config.min_lot_size} lots)."
            )

        # 4. Mandatory Stop Loss Check
        if self.config.require_stop_loss and order.sl is None:
            raise RiskViolationError(
                "ORDER REJECTED: Stop Loss is mandatory. Never trade without SL protection."
            )

        # 5. Max Concurrent Positions Check
        if current_open_positions_count >= self.config.max_open_positions:
            raise RiskViolationError(
                f"ORDER REJECTED: Max open positions limit ({self.config.max_open_positions}) reached."
            )

        # 6. Anti-Flood / Infinite Loop Protection
        self._check_rate_limit()

        logger.info(f"Risk checks PASSED for {order.symbol} ({order.volume} lots, SL={order.sl})")

    def trigger_kill_switch(self, reason: str):
        """Manually or automatically locks all trading operations."""
        self.kill_switch_active = True
        self.kill_switch_reason = reason
        logger.critical(f"[KILL-SWITCH ACTIVATED] {reason}")

    def reset_kill_switch(self):
        """Admin override to reset the circuit breaker."""
        self.kill_switch_active = False
        self.kill_switch_reason = ""
        logger.info("Kill-switch reset by administrator.")

    def _check_rate_limit(self):
        """Ensures the bot does not spam orders in an unexpected loop."""
        now = time.time()
        # Keep only timestamps from the last 60 seconds
        self._order_timestamps = [t for t in self._order_timestamps if now - t < 60]

        if len(self._order_timestamps) >= self.config.max_orders_per_minute:
            self.trigger_kill_switch("High-frequency order flood detected (Infinite Loop Risk)")
            raise RiskViolationError("EMERGENCY: Too many orders submitted within 60 seconds. Circuit breaker tripped.")

        self._order_timestamps.append(now)

    def _check_daily_drawdown(self, account_summary):
        """Calculates current equity drawdown relative to day-start balance."""
        today = datetime.utcnow().date()
        if today != self._day_start_date or self._initial_day_balance is None:
            self._day_start_date = today
            self._initial_day_balance = account_summary.balance

        if self._initial_day_balance > 0:
            loss = self._initial_day_balance - account_summary.equity
            loss_pct = (loss / self._initial_day_balance) * 100

            if loss_pct >= self.config.max_daily_drawdown_pct:
                self.trigger_kill_switch(f"Daily drawdown threshold reached: {loss_pct:.2f}% (Limit: {self.config.max_daily_drawdown_pct}%)")
                raise RiskViolationError(f"Daily drawdown limit of {self.config.max_daily_drawdown_pct}% breached.")
