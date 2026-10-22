"""
Example 02: Place a Market Buy order with Stop Loss and Take Profit.
"""

from ctrader_trader import CTraderClient, TradeOrder, OrderType

if __name__ == "__main__":
    client = CTraderClient()
    client.connect()

    # Create market order
    buy_order = TradeOrder(
        symbol="EURUSD",
        order_type=OrderType.BUY,
        volume=0.10,       # 0.10 lot
        sl=1.08200,        # Stop Loss
        tp=1.09200,        # Take Profit
        comment="Market Scalper"
    )

    print(f"Submitting {buy_order.order_type.value} on {buy_order.symbol} for {buy_order.volume} lot(s)...")
    response = client.place_order(buy_order)

    if response.success:
        print(f"Success! Order ID: {response.order_id} | Position ID: {response.position_id}")
        print(f"Executed at Price: {response.executed_price}")
    else:
        print(f"Failed: {response.message} (Code: {response.error_code})")
