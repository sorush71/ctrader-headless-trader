# cTrader Headless Trader 🚀

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![API](https://img.shields.io/badge/cTrader-Open%20API-green.svg)](https://portal.ctrader.com/)
[![Trading](https://img.shields.io/badge/Headless-No%20GUI-orange.svg)]()

A production-ready, lightweight, and modular Python library for algorithmic Forex trading via the official **cTrader Open API**. 

Designed specifically for headless environments, allowing automated trading directly on basic Linux hosts, Raspberry Pi, Docker, or serverless functions **without requiring MetaTrader, without Windows servers, and with zero GUI overhead.**

---

## 🌟 Key Features

- **100% Cloud-Native & Free:** Direct connection to Spotware's official cloud gateway (`openapi.ctrader.com`) with zero server license fees.
- **Headless & Ultra-Lightweight:** Runs seamlessly on low-resource VPS (512MB RAM), basic shared hosting with Python, or Docker containers.
- **Pure Python Protocol Engine:** Built-in 4-byte big-endian framing and Google Protocol Buffers (`Protobuf`) wire-format parser. No legacy C-extensions or deprecated Twisted dependencies required.
- **Integrated Risk Management Gate (Circuit Breakers):**
  - **Hard Lot Cap:** Enforces maximum volume per order to eliminate fat-finger errors.
  - **Mandatory Stop Loss:** Refuses to send any unprotected market or pending orders.
  - **Daily Drawdown Kill-Switch:** Automatically freezes trading if daily loss exceeds configured threshold.
  - **Anti-Flood Rate Limiting:** Detects and halts runaway infinite order loops.
  - **Emergency Stop:** Instant programmatic kill-switch to shut down all operations.
- **Complete Order Lifecycle:** Market execution (`BUY / SELL`), pending orders (`Limit / Stop`), position close, order modification, and order cancellation.

---

## 📁 Project Structure

```text
ctrader-headless-trader/
├── ctrader_trader/
│   ├── __init__.py          # Package exports and versioning
│   ├── models.py            # Dataclasses and Enums (TradeOrder, TradeResponse, OrderType)
│   ├── config.py            # Environment and credential management
│   ├── protocol.py          # Binary Protobuf encoder/decoder & length-prefixed TLS framing
│   ├── gateway.py           # TLS socket transport (port 5035) & heartbeat keep-alive
│   ├── risk.py              # Financial safety supervisor & circuit breaker engine
│   └── client.py            # High-level trading client interface
├── examples/
│   ├── 01_check_balance.py            # Fetch balance, equity, and leverage
│   ├── 02_market_order.py             # Place market order with SL and TP
│   ├── 03_pending_order_cancel.py     # Place and cancel pending limit orders
│   └── 04_safety_guardrails_test.py   # Test circuit breakers and risk filters
├── .env.example             # Environment variable template
├── .gitignore
├── requirements.txt
├── setup.py
└── README.md
```

---

## 🛠 Installation

```bash
git clone https://github.com/sorush71/ctrader-headless-trader.git
cd ctrader-headless-trader
pip install -r requirements.txt
```

---

## 🔑 Obtaining Free cTrader API Credentials

1. Register or sign in at the official developer portal: [portal.ctrader.com](https://portal.ctrader.com).
2. Create an Application to receive your `Client ID` and `Client Secret`.
3. Generate an `Access Token` linked to your cTrader demo or live trading account.
4. Copy `.env.example` to `.env` and fill in your keys:

```env
CTRADER_CLIENT_ID=your_client_id_here
CTRADER_CLIENT_SECRET=your_client_secret_here
CTRADER_ACCESS_TOKEN=your_access_token_here
CTRADER_ACCOUNT_ID=12345678
CTRADER_ENVIRONMENT=demo
```

> **Note:** If no credentials are provided in `.env`, the library automatically operates in **Safe Sandbox Mode**, simulating orders and responses for testing and development.

---

## 💻 Quick Start

### 1. Account Summary
```python
from ctrader_trader import CTraderClient

client = CTraderClient()
client.connect()

summary = client.get_account_summary()
print(f"Balance: ${summary.balance:,.2f} {summary.currency} | Equity: ${summary.equity:,.2f}")
```

### 2. Placing an Order with Risk Protection
```python
from ctrader_trader import CTraderClient, TradeOrder, OrderType, RiskConfig

# Initialize with strict risk guardrails
client = CTraderClient(
    risk_config=RiskConfig(
        max_lot_size=0.50,         # Maximum 0.50 lot per order
        require_stop_loss=True,     # Stop Loss is mandatory
        max_daily_drawdown_pct=3.0  # Emergency stop at 3% loss
    )
)
client.connect()

# Submit Market Buy order
order = TradeOrder(
    symbol="EURUSD",
    order_type=OrderType.BUY,
    volume=0.10,
    sl=1.08200,
    tp=1.09200,
    comment="Headless Python Bot"
)

response = client.place_order(order)
if response.success:
    print(f"Order Executed! Order ID: {response.order_id} at {response.executed_price}")
else:
    print(f"Rejected: {response.message} (Code: {response.error_code})")
```

---

## 🛡️ Risk Management & Circuit Breakers

The built-in `RiskManager` intercepts every trade before transmission to the broker:

| Guardrail | Default Value | Description |
| :--- | :--- | :--- |
| **Max Lot Cap** | `0.50 lots` | Rejects any order exceeding volume limit |
| **Mandatory Stop Loss** | `True` | Disallows any order without an explicit `sl` parameter |
| **Daily Drawdown Limit** | `4.0%` | Trips the kill-switch if day losses reach threshold |
| **Anti-Flood Rate Limit** | `5 orders/min` | Shuts down execution if loop spam is detected |
| **Max Concurrent Trades** | `3 positions` | Limits open exposure on the account |

---

<br>

---

## 🇮🇷 راهنمای فارسی (Persian Documentation)

### معرفی پروژه
این پروژه یک کتابخانه مستقل، سبک و استاندارد پایتون برای اتصال مستقیم به **cTrader Open API** و اجرای معاملات خودکار در بازار فارکس بدون نیاز به متاتریدر و سرور ویندوزی است.

### چرا این پروژه اهمیت دارد؟
- **حذف هزینه‌های سرور:** بر خلاف متاتریدر که نیاز به سرور ویندوزی سنگین و اجرای مداوم برنامه دارد، این کتابخانه به صورت Headless (بدون محیط گرافیکی) حتی روی هاست‌های ساده لینوکسی، داکر یا رزبری‌پای کار می‌کند.
- **پروتکل ارتباطی مستقیم:** ارتباط با سرور ابری رسمی بروکر از طریق سوکت امن TLS روی پورت ۵۰۳۵ با پروتکل باینری Google Protobuf برقرار می‌شود.
- **سیستم ایمنی و ترمز اضطراری (Circuit Breaker):** مجهز به محافظت سخت‌افزاری در برابر حجم‌های بالا، اجباری بودن حد ضرر، سقف ضرر روزانه و جلوگیری از لوپ زدن اردرها برای حفظ قطعی سرمایه.

### نحوه راه‌اندازی سریع
۱. پروژه را کلون کرده و پیش‌نیازها را نصب کنید:
```bash
git clone https://github.com/sorush71/ctrader-headless-trader.git
cd ctrader-headless-trader
pip install -r requirements.txt
```
۲. فایل `.env.example` را به `.env` تغییر نام داده و اطلاعات کلیدهای دریافتی از [portal.ctrader.com](https://portal.ctrader.com) را وارد کنید.  
۳. اسکریپت‌های نمونه در پوشه `examples/` را اجرا کنید:
- `01_check_balance.py`: مشاهده بالانس و مارجین.
- `02_market_order.py`: ثبت سفارش خرید و فروش با حد سود و ضرر.
- `03_pending_order_cancel.py`: ثبت سفارش لیمیت و لغو آن.
- `04_safety_guardrails_test.py`: تست گاردریل‌های ایمنی و ترمز اضطراری.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
