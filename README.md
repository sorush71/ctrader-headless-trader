# cTrader Headless Trader (Python) 🚀

یک کتابخانه سبک، ماژولار و مستقل پایتون برای معامله‌گری خودکار در بازار فارکس بر بستر رسمی **cTrader Open API**، بدون نیاز به نصب متاتریدر، بدون نیاز به سرور ویندوزی و بدون محیط گرافیکی.

---

## 🌟 ویژگی‌ها (Key Features)

- **کاملاً رایگان و ابری:** اتصال مستقیم به `Open API` شرکت `Spotware` بدون یک ریال هزینه سرور یا لایسنس.
- **بدون محیط گرافیکی (Headless):** قابل اجرا روی ارزان‌ترین هاست‌های لینوکسی، رزبری‌پای، داکر یا توابع `Serverless`.
- **مدیریت کامل سفارشات:** پشتیبانی از سفارش‌های مارکت (`BUY / SELL`)، سفارش‌های معلق (`Limit / Stop`)، لغو سفارش و بستن پوزیشن.
- **مدیریت ریسک:** تنظیم دقیق حجم (لات)، حد ضرر (`Stop Loss`) و حد سود (`Take Profit`).
- **معماری ماژولار و مدرن:** پیاده‌سازی شده با پایتون ۳.۱۰+ و تایپ‌هینتینگ کامل (`Type Hints`).

---

## 📁 ساختار پروژه (Project Structure)

```text
ctrader-headless-trader/
├── ctrader_trader/
│   ├── __init__.py
│   ├── models.py           # مدل‌های داده و Enumهای سفارشات
│   ├── config.py           # مدیریت تنظیمات و اعتبارسنجی
│   ├── client.py           # کلاس اصلی کلاینت معاملاتی
│   └── gateway.py          # مدیریت پروتکل شبکه و وب‌سوکت
├── examples/
│   ├── 01_check_balance.py         # دریافت اطلاعات حساب
│   ├── 02_market_order.py          # ارسال اردر مارکت با SL/TP
│   └── 03_pending_order_cancel.py  # ثبت اردر پندینگ و لغو آن
├── .env.example            # نمونه فایل متغیرهای محیطی
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🛠 پیش‌نیازها و نصب (Installation)

```bash
git clone https://github.com/your-username/ctrader-headless-trader.git
cd ctrader-headless-trader
pip install -r requirements.txt
```

---

## 🔑 نحوه دریافت رایگان کلیدهای API از cTrader

1. به پرتال رسمی توسعه‌دهندگان cTrader به آدرس [portal.ctrader.com](https://portal.ctrader.com) بروید و وارد شوید.
2. یک اپلیکیشن جدید بسازید تا `Client ID` و `Client Secret` دریافت کنید.
3. فایل `.env.example` را به `.env` کپی کرده و اطلاعات خود را وارد کنید:

```env
CTRADER_CLIENT_ID=your_client_id_here
CTRADER_CLIENT_SECRET=your_client_secret_here
CTRADER_ACCESS_TOKEN=your_access_token_here
CTRADER_ACCOUNT_ID=your_account_id_here
CTRADER_ENVIRONMENT=demo
```

---

## 💻 نمونه استفاده سریع (Quick Start)

```python
from ctrader_trader.client import CTraderClient
from ctrader_trader.models import TradeOrder, OrderType

# ۱. راه‌اندازی کلاینت
client = CTraderClient()
client.connect()

# ۲. مشاهده موجودی حساب
account = client.get_account_summary()
print(f"Balance: {account.balance} {account.currency} | Equity: {account.equity}")

# ۳. ارسال سفارش خرید مارکت (EURUSD) با حجم 0.1 لات
order = TradeOrder(
    symbol="EURUSD",
    order_type=OrderType.BUY,
    volume=0.10,
    sl=1.08200,
    tp=1.09200,
    comment="Headless Python Bot"
)
response = client.place_order(order)
print(f"Order Executed! Order ID: {response.order_id} at {response.executed_price}")
```
