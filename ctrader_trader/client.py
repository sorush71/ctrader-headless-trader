import logging
from typing import Optional
from .config import CTraderConfig
from .models import TradeOrder, TradeResponse, AccountSummary, OrderType
from .gateway import CTraderGateway
from .protocol import ProtoOrderType, TradeSide
from .risk import RiskManager, RiskConfig, RiskViolationError

logger = logging.getLogger("cTraderClient")


class CTraderClient:
    """
    High-level headless trading client for cTrader Open API with built-in Risk Management.
    Enforces circuit breakers, max lot caps, mandatory SL, and anti-loop safety.
    """

    SYMBOL_MAP = {
        "EURUSD": 1,
        "GBPUSD": 2,
        "USDJPY": 3,
        "USDCHF": 4,
        "AUDUSD": 5,
        "USDCAD": 6,
        "NZDUSD": 7,
        "XAUUSD": 8,  # Gold
        "BTCUSD": 22396
    }

    def __init__(self, config: Optional[CTraderConfig] = None, risk_config: Optional[RiskConfig] = None):
        self.config = config or CTraderConfig.from_env()
        self.gateway = CTraderGateway(self.config)
        self.risk_manager = RiskManager(risk_config)
        self._active_positions_count = 0

    def connect(self) -> bool:
        """Connects and authorizes with cTrader Open API."""
        return self.gateway.connect()

    def disconnect(self):
        """Disconnects session and stops heartbeat worker."""
        self.gateway.disconnect()

    def get_account_summary(self) -> AccountSummary:
        """Fetches account balance, equity, and margin details."""
        raw = self.gateway.get_trader_info()
        return AccountSummary(
            account_id=str(raw["accountId"]),
            balance=float(raw["balance"]),
            equity=float(raw["equity"]),
            free_margin=float(raw["freeMargin"]),
            margin_used=float(raw["marginUsed"]),
            leverage=int(raw.get("leverage", 100)),
            currency=raw.get("currency", "USD")
        )

    def place_order(self, order: TradeOrder) -> TradeResponse:
        """
        Places a Market, Limit, or Stop order with volume, SL, and TP.
        Enforces strict pre-trade risk validation and financial circuit breakers.
        """
        try:
            self._validate_order(order)

            # 0. Risk Management Pre-Trade Gate
            account_summary = self.get_account_summary()
            self.risk_manager.validate_order(
                order=order,
                account_summary=account_summary,
                current_open_positions_count=self._active_positions_count
            )

            # 1. Map Symbol
            symbol_upper = order.symbol.upper()
            symbol_id = self.SYMBOL_MAP.get(symbol_upper, 1)

            # 2. Map Order Type
            if order.order_type in [OrderType.BUY, OrderType.SELL]:
                p_order_type = ProtoOrderType.MARKET
            elif order.order_type in [OrderType.BUY_LIMIT, OrderType.SELL_LIMIT]:
                p_order_type = ProtoOrderType.LIMIT
            elif order.order_type in [OrderType.BUY_STOP, OrderType.SELL_STOP]:
                p_order_type = ProtoOrderType.STOP
            else:
                p_order_type = ProtoOrderType.MARKET

            # 3. Map Side
            p_side = TradeSide.BUY if "BUY" in order.order_type.value else TradeSide.SELL

            # 4. Convert lot volume to cents (1 lot = 100,000 units = 10,000,000 cents)
            volume_cents = int(order.volume * 100_000 * 100)

            res = self.gateway.send_order(
                symbol_id=symbol_id,
                order_type=p_order_type,
                side=p_side,
                volume_cents=volume_cents,
                price=order.price,
                sl=order.sl,
                tp=order.tp,
                comment=order.comment
            )
            self._active_positions_count += 1
            return TradeResponse(
                success=True,
                order_id=res.get("orderId"),
                position_id=res.get("positionId"),
                executed_price=res.get("executionPrice") or order.price,
                message="Order dispatched via cTrader Open API (Risk Checked)"
            )
        except RiskViolationError as rve:
            logger.warning(f"Trade blocked by RiskManager: {rve}")
            return TradeResponse(success=False, error_code="RISK_VIOLATION", message=str(rve))
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return TradeResponse(success=False, error_code="EXECUTION_FAILED", message=str(e))

    def cancel_order(self, order_id: int) -> bool:
        """Cancels an existing pending order (Limit or Stop)."""
        return self.gateway.cancel_order(order_id)

    def close_position(self, position_id: int, volume: Optional[float] = None) -> TradeResponse:
        """Closes an open position fully or partially."""
        volume_cents = int(volume * 100_000 * 100) if volume else None
        res = self.gateway.close_position(position_id, volume_cents)
        self._active_positions_count = max(0, self._active_positions_count - 1)
        return TradeResponse(
            success=True,
            position_id=position_id,
            executed_price=res.get("closePrice"),
            message="Position closed successfully"
        )

    def emergency_stop(self, reason: str = "Manual Emergency Stop"):
        """Instantly trips the circuit breaker and blocks all subsequent orders."""
        self.risk_manager.trigger_kill_switch(reason)

    def _validate_order(self, order: TradeOrder):
        """Sanity checks for order inputs before sending to the broker."""
        if order.volume <= 0:
            raise ValueError("Order volume (lots) must be strictly greater than 0.")
        if order.order_type in [OrderType.BUY_LIMIT, OrderType.SELL_LIMIT, OrderType.BUY_STOP, OrderType.SELL_STOP]:
            if order.price is None:
                raise ValueError(f"Price is mandatory for pending order type: {order.order_type.value}")
