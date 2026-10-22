"""
Example 03: Place a Pending Limit order, then cancel it.
"""

from ctrader_trader import CTraderClient, TradeOrder, OrderType

if __name__ == "__main__":
    client = CTraderClient()
    client.connect()

    # 1. Place a Buy Limit on Gold
    gold_limit = TradeOrder(
        symbol="XAUUSD",
        order_type=OrderType.BUY_LIMIT,
        volume=0.05,
        price=2680.50,
        sl=2660.00,
        tp=2720.00,
        comment="Dip Buyer"
    )

    print(f"Placing Buy Limit at ${gold_limit.price}...")
    res = client.place_order(gold_limit)
    print(f"Limit order confirmed with Order ID: {res.order_id}")

    # 2. Cancel the pending order
    print(f"Cancelling order {res.order_id}...")
    cancelled = client.cancel_order(res.order_id)
    if cancelled:
        print("Order successfully cancelled without touching any GUI!")
