from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime


class OrderType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"


@dataclass
class TradeOrder:
    symbol: str
    order_type: OrderType
    volume: float  # In lots (e.g. 0.01, 0.1, 1.0)
    price: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    comment: str = "Headless CTrader Bot"
    client_order_id: Optional[str] = None


@dataclass
class TradeResponse:
    success: bool
    order_id: Optional[int] = None
    position_id: Optional[int] = None
    executed_price: Optional[float] = None
    error_code: Optional[str] = None
    message: Optional[str] = None
    timestamp: str = datetime.utcnow().isoformat()


@dataclass
class AccountSummary:
    account_id: str
    balance: float
    equity: float
    free_margin: float
    margin_used: float
    leverage: int
    currency: str
