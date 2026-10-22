import logging
from typing import Optional
from .config import CTraderConfig
from .models import TradeOrder, TradeResponse, AccountSummary, OrderType
from .gateway import CTraderGateway

logger = logging.getLogger("cTraderClient")


class CTraderClient:
    """
    High-level headless trading client for cTrader Open API.
    Designed to run on lightweight Linux servers, Docker, or basic Python hosts.
    """

    def __init__(self, config: Optional[CTraderConfig] = None):
        self.config = config or CTraderConfig.from_env()
        self.gateway = CTraderGateway(self.config)

    def connect(self) -> bool:
        """Connects and authorizes with cTrader Open API."""
        return self.gateway.connect()

    def get_account_summary(self) -> AccountSummary:
        """Fetches account balance, equity, and margin details."""
        raw = self.gateway.fetch_trader_info()
        return AccountSummary(
            account_id=str(raw["accountId"]),
            balance=float(raw["balance"]),
            equity=float(raw["equity"]),
            free_margin=float(raw["freeMargin"]),
            margin_used=float(raw["marginUsed"]),
            leverage=int(raw["leverageInCents"] / 100),
            currency=raw["currency"]
        )

    def place_order(self, order: TradeOrder) -> TradeResponse:
        """
        Places a Market, Limit, or Stop order with volume, SL, and TP.
        """
        self._validate_order(order)
        
        # cTrader specifies volume in cents/units (e.g. 1 lot EURUSD = 100,000 units = 10,000,000 cents)
        volume_in_cents = int(order.volume * 100_000 * 100)

        payload = {
            "symbol": order.symbol,
            "orderType": order.order_type.value,
            "volume": volume_in_cents,
            "price": order.price,
            "stopLoss": order.sl,
            "takeProfit": order.tp,
            "comment": order.comment
        }

        try:
            res = self.gateway.send_order_payload(payload)
            return TradeResponse(
                success=True,
                order_id=res.get("orderId"),
                position_id=res.get("positionId"),
                executed_price=res.get("executionPrice"),
                message="Order executed successfully via cTrader Open API"
            )
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return TradeResponse(success=False, error_code="EXECUTION_FAILED", message=str(e))

    def cancel_order(self, order_id: int) -> bool:
        """Cancels an existing pending order (Limit or Stop)."""
        return self.gateway.cancel_order_payload(order_id)

    def close_position(self, position_id: int, volume: Optional[float] = None) -> TradeResponse:
        """Closes an open position fully or partially."""
        volume_cents = int(volume * 100_000 * 100) if volume else None
        res = self.gateway.close_position_payload(position_id, volume_cents)
        return TradeResponse(
            success=True,
            position_id=position_id,
            executed_price=res.get("closePrice"),
            message="Position closed successfully"
        )

    def _validate_order(self, order: TradeOrder):
        """Sanity checks for order inputs before sending to the broker."""
        if order.volume <= 0:
            raise ValueError("Order volume (lots) must be strictly greater than 0.")
        if order.order_type in [OrderType.BUY_LIMIT, OrderType.SELL_LIMIT, OrderType.BUY_STOP, OrderType.SELL_STOP]:
            if order.price is None:
                raise ValueError(f"Price is mandatory for pending order type: {order.order_type.value}")
