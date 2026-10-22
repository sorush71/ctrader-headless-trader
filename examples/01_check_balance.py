"""
Example 01: Connect and check live account balance without GUI.
"""

from ctrader_trader import CTraderClient

if __name__ == "__main__":
    client = CTraderClient()
    client.connect()

    account = client.get_account_summary()
    print("-" * 50)
    print(f"cTrader Account ID: {account.account_id}")
    print(f"Balance:           ${account.balance:,.2f} {account.currency}")
    print(f"Equity:            ${account.equity:,.2f} {account.currency}")
    print(f"Free Margin:       ${account.free_margin:,.2f} {account.currency}")
    print(f"Leverage:          1:{account.leverage}")
    print("-" * 50)
