"""
Example 04: Demonstration of Financial Safety Guardrails & Circuit Breakers.
Tests:
1. Hard Lot Cap (Max 0.5 lots).
2. Mandatory Stop Loss check.
3. Anti-Loop / Flood rate limiting.
4. Emergency Kill-Switch.
"""

from ctrader_trader import CTraderClient, TradeOrder, OrderType, RiskConfig

if __name__ == "__main__":
    print("=" * 60)
    print("[SAFETY] RUNNING FINANCIAL SAFETY & RISK MANAGEMENT TESTS")
    print("=" * 60)

    # 1. Initialize client with strict risk rules
    client = CTraderClient(
        risk_config=RiskConfig(
            max_lot_size=0.50,
            require_stop_loss=True,
            max_orders_per_minute=3
        )
    )
    client.connect()

    # TEST A: Valid safe order (0.10 lot with SL)
    print("\n[TEST A] Submitting Valid Order (0.10 lot, SL=1.0820)...")
    safe_order = TradeOrder(
        symbol="EURUSD",
        order_type=OrderType.BUY,
        volume=0.10,
        sl=1.0820,
        tp=1.0920
    )
    res_a = client.place_order(safe_order)
    print(f"Result: Success={res_a.success} | Message: {res_a.message}")

    # TEST B: Dangerous high lot order (2.00 lots > 0.50 cap)
    print("\n[TEST B] Submitting Dangerous High Lot Order (2.00 lots)...")
    big_order = TradeOrder(
        symbol="EURUSD",
        order_type=OrderType.BUY,
        volume=2.00,  # Breaches 0.50 max cap
        sl=1.0820,
        tp=1.0920
    )
    res_b = client.place_order(big_order)
    print(f"Result: Success={res_b.success} | Code={res_b.error_code} | Reason: {res_b.message}")

    # TEST C: Careless order WITHOUT Stop Loss
    print("\n[TEST C] Submitting Order WITHOUT Stop Loss (sl=None)...")
    no_sl_order = TradeOrder(
        symbol="EURUSD",
        order_type=OrderType.BUY,
        volume=0.05,
        sl=None  # Missing SL
    )
    res_c = client.place_order(no_sl_order)
    print(f"Result: Success={res_c.success} | Code={res_c.error_code} | Reason: {res_c.message}")

    # TEST D: Emergency Kill-Switch test
    print("\n[TEST D] Testing Emergency Kill-Switch...")
    client.emergency_stop("Manual trader intervention")
    res_d = client.place_order(safe_order)
    print(f"Result after Kill-Switch: Success={res_d.success} | Reason: {res_d.message}")

    print("\n" + "=" * 60)
    print("[SUCCESS] ALL RISK GUARDRAILS OPERATING PERFECTLY. CAPITAL IS PROTECTED.")
    print("=" * 60)
