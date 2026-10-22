"""
cTrader Headless Trader
A modern Python package for algorithmic trading on cTrader Open API without a GUI.
"""

from .client import CTraderClient
from .models import OrderType, TradeOrder, TradeResponse, AccountSummary
from .risk import RiskManager, RiskConfig, RiskViolationError

__all__ = [
    "CTraderClient",
    "OrderType",
    "TradeOrder",
    "TradeResponse",
    "AccountSummary",
    "RiskManager",
    "RiskConfig",
    "RiskViolationError"
]
__version__ = "1.0.0"
