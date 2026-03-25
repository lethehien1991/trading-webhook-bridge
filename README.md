# TradingView → Telegram Webhook Bridge

Flask server nhận webhook alert từ TradingView và forward đến Telegram Bot.

## Endpoints

| Method | Path | Mô tả |
|--------|------|--------|
| `POST` | `/webhook` | Nhận alert từ TradingView |
| `GET` | `/health` | Health check |
| `GET` | `/test` | Gửi test message đến Telegram |

---

## Deploy lên Railway

### Bước 1 — Push lên GitHub

```bash
# Tạo repo mới trên GitHub, sau đó:
git remote add origin https://github.com/YOUR_USERNAME/trading-webhook-bridge.git
git push -u origin main
```

### Bước 2 — Deploy trên Railway

1. Vào [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
2. Chọn repo `trading-webhook-bridge`
3. Railway tự detect `Procfile` và deploy

### Bước 3 — Set Environment Variables trên Railway

Vào **Variables** tab, thêm:

```
TELEGRAM_BOT_TOKEN=8674328773:AAHZ_...
TELEGRAM_CHAT_ID=1587450441
SECRET_KEY=myTradingSecret123XYZ
```

### Bước 4 — Lấy Public URL

Railway cấp URL dạng: `https://trading-webhook-bridge-production.up.railway.app`

Verify bằng cách mở: `https://YOUR_URL/health`

---

## Cấu hình TradingView Alert

1. Mở TradingView → tạo Alert
2. **Webhook URL:**
   ```
   https://YOUR_URL/webhook?secret=myTradingSecret123XYZ
   ```
3. **Message** (JSON body):
   ```json
   {
     "pair": "{{ticker}}",
     "time": "{{time}}",
     "timeframe": "{{interval}}",
     "entry": "{{close}}",
     "stop_loss": "{{plot_0}}",
     "target": "{{plot_1}}",
     "rr": "2.0:1",
     "position_size": "1.5%"
   }
   ```
4. Bật **Send webhook notifications**

---

## Local Development

```bash
# 1. Tạo virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Cài dependencies
pip install -r requirements.txt

# 3. Copy env file
cp .env.example .env
# Điền token, chat_id, secret vào .env

# 4. Chạy server
python webhook_bridge.py

# 5. Test
python test_webhook.py
```

---

## Message Format

```
🎯 SWING LOW SETUP DETECTED
━━━━━━━━━━━━━━━━━━━━━━━
📊 Pair:       BTCUSDT
🕐 Time:       2024-01-15 08:30 UTC
⏱ Timeframe:  4H
━━━━━━━━━━━━━━━━━━━━━━━
📈 TRADE SETUP
  🟢 Entry:         65,420.00
  🔴 Stop Loss:     64,800.00
  🎯 Target:        66,660.00
  ⚖️ R:R Ratio:     2.0:1
  📦 Position Size: 1.5%
━━━━━━━━━━━━━━━━━━━━━━━
✅ CONDITIONS MET
  ✅ Swing Low Identified
  ✅ Higher Timeframe Support
  ✅ Volume Spike Confirmed
  ✅ RSI Oversold Recovery
  ✅ EMA Stack Alignment
  ✅ Candle Pattern Valid
  ✅ Risk/Reward >= 2:1
━━━━━━━━━━━━━━━━━━━━━━━
📉 View Chart on TradingView
```
