"""
Test Script — TradingView Webhook Bridge
Chạy: python test_webhook.py
"""

import requests
import json
from datetime import datetime

import os
from dotenv import load_dotenv

load_dotenv()  # đọc từ file .env nếu có

# ─── Config (từ environment variables) ───────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
SECRET_KEY         = os.environ.get("SECRET_KEY", "")
LOCAL_SERVER       = os.environ.get("LOCAL_SERVER", "http://localhost:5000")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ ERROR: Thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID trong .env")
    print("   Copy .env.example → .env và điền thông tin vào.")
    exit(1)

TELEGRAM_API_URL   = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


# ─── Test 1: Direct Telegram API ─────────────────────────────────────────────
def test_telegram_direct():
    """Gửi message trực tiếp qua Telegram API (không qua Flask server)."""
    print("\n" + "="*60)
    print("TEST 1: Direct Telegram API")
    print("="*60)

    message = (
        "🔔 <b>Test từ Webhook Bridge</b>\n\n"
        "✅ Kết nối Telegram thành công!\n"
        f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        "Bot đã sẵn sàng nhận alert từ TradingView."
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        resp = requests.post(TELEGRAM_API_URL, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("ok"):
            print(f"✅ SUCCESS — Message ID: {data['result']['message_id']}")
        else:
            print(f"❌ FAILED — {data}")
    except Exception as e:
        print(f"❌ ERROR — {e}")


# ─── Test 2: Health Check ─────────────────────────────────────────────────────
def test_health_endpoint():
    """Kiểm tra Flask server đang chạy."""
    print("\n" + "="*60)
    print("TEST 2: Health Check — GET /health")
    print("="*60)

    try:
        resp = requests.get(f"{LOCAL_SERVER}/health", timeout=5)
        data = resp.json()
        print(f"✅ Status: {resp.status_code}")
        print(f"   Response: {json.dumps(data, indent=4)}")
    except requests.ConnectionError:
        print(f"⚠️  Server not running at {LOCAL_SERVER}")
        print("   Chạy: python webhook_bridge.py trước, rồi test lại.")
    except Exception as e:
        print(f"❌ ERROR — {e}")


# ─── Test 3: Webhook POST ─────────────────────────────────────────────────────
def test_webhook_endpoint():
    """Gửi sample TradingView alert đến /webhook endpoint."""
    print("\n" + "="*60)
    print("TEST 3: Webhook POST — POST /webhook")
    print("="*60)

    sample_payload = {
        "secret":        SECRET_KEY,
        "pair":          "BTCUSDT",
        "time":          datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "timeframe":     "4H",
        "entry":         "65,420.00",
        "stop_loss":     "64,800.00",
        "target":        "66,660.00",
        "rr":            "2.0:1",
        "position_size": "1.5%",
        "chart_link":    "https://www.tradingview.com/chart/?symbol=BINANCE:BTCUSDT",
        "cond1":         "Swing Low Identified ✓",
        "cond2":         "HTF Support @ 64,500",
        "cond3":         "Volume Spike +340%",
        "cond4":         "RSI 28 → 35 Recovery",
        "cond5":         "EMA 21/50/200 Aligned",
        "cond6":         "Bullish Engulfing Candle",
        "cond7":         "R:R = 2.0:1 ✓",
    }

    print(f"📤 Payload:\n{json.dumps(sample_payload, indent=4)}\n")

    try:
        resp = requests.post(
            f"{LOCAL_SERVER}/webhook",
            json=sample_payload,
            timeout=15,
        )
        data = resp.json()
        print(f"✅ Status: {resp.status_code}")
        print(f"   Response: {json.dumps(data, indent=4)}")
    except requests.ConnectionError:
        print(f"⚠️  Server not running at {LOCAL_SERVER}")
        print("   Chạy: python webhook_bridge.py trước, rồi test lại.")
    except Exception as e:
        print(f"❌ ERROR — {e}")


# ─── Test 4: Unauthorized Request ────────────────────────────────────────────
def test_unauthorized():
    """Verify server từ chối request không có secret key."""
    print("\n" + "="*60)
    print("TEST 4: Security Check — Wrong Secret Key")
    print("="*60)

    try:
        resp = requests.post(
            f"{LOCAL_SERVER}/webhook",
            json={"pair": "BTCUSDT", "secret": "wrong_key"},
            timeout=5,
        )
        if resp.status_code == 401:
            print("✅ PASS — Server correctly rejected unauthorized request (401)")
        else:
            print(f"⚠️  Unexpected status: {resp.status_code} — {resp.json()}")
    except requests.ConnectionError:
        print(f"⚠️  Server not running at {LOCAL_SERVER}")
    except Exception as e:
        print(f"❌ ERROR — {e}")


# ─── Test 5: /test Endpoint ───────────────────────────────────────────────────
def test_test_endpoint():
    """Gọi GET /test để server tự gửi sample alert đến Telegram."""
    print("\n" + "="*60)
    print("TEST 5: Test Endpoint — GET /test")
    print("="*60)

    try:
        resp = requests.get(f"{LOCAL_SERVER}/test", timeout=15)
        data = resp.json()
        print(f"✅ Status: {resp.status_code}")
        print(f"   Response: {json.dumps(data, indent=4)}")
    except requests.ConnectionError:
        print(f"⚠️  Server not running at {LOCAL_SERVER}")
    except Exception as e:
        print(f"❌ ERROR — {e}")


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 TradingView Webhook Bridge — Test Suite")
    print(f"   Bot Token : {TELEGRAM_BOT_TOKEN[:20]}...")
    print(f"   Chat ID   : {TELEGRAM_CHAT_ID}")
    print(f"   Server    : {LOCAL_SERVER}")

    # Test 1 không cần Flask server
    test_telegram_direct()

    # Test 2–5 cần Flask server đang chạy
    test_health_endpoint()
    test_webhook_endpoint()
    test_unauthorized()
    test_test_endpoint()

    print("\n" + "="*60)
    print("✅ Test suite hoàn thành!")
    print("="*60)
