"""
TradingView → Telegram Webhook Bridge
Nhận alert từ TradingView và forward đến Telegram Bot
"""

import os
import logging
import requests
from flask import Flask, request, jsonify
from datetime import datetime

# ─── Logging Setup ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ─── App Init ────────────────────────────────────────────────────────────────
app = Flask(__name__)

# ─── Environment Variables ───────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
SECRET_KEY         = os.environ.get("SECRET_KEY", "")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


# ─── Helper: Send Telegram Message ───────────────────────────────────────────
def send_telegram_message(text: str) -> dict:
    """Gửi message đến Telegram với parse_mode HTML."""
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(TELEGRAM_API_URL, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info("✅ Telegram message sent successfully")
        return resp.json()
    except requests.RequestException as e:
        logger.error(f"❌ Failed to send Telegram message: {e}")
        raise


# ─── Helper: Format Alert Message ────────────────────────────────────────────
def format_alert_message(data: dict) -> str:
    """Tạo HTML message đẹp từ TradingView alert data."""

    pair       = data.get("pair", "N/A")
    time_str   = data.get("time", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
    timeframe  = data.get("timeframe", "N/A")
    signal     = data.get("signal", "").upper()   # LONG / SHORT

    entry      = data.get("entry", "N/A")
    stop_loss  = data.get("stop_loss", "N/A")
    target     = data.get("target", "N/A")
    rr         = data.get("rr", "N/A")
    pos_size   = data.get("position_size", "N/A")

    chart_link = data.get("chart_link", f"https://www.tradingview.com/chart/?symbol={pair}")

    # Header & emoji theo hướng LONG / SHORT
    if signal == "LONG":
        header     = "🟢 <b>LONG SIGNAL DETECTED</b>"
        dir_emoji  = "📈"
        entry_icon = "🟢"
        sl_icon    = "🔴"
        tp_icon    = "🎯"
    elif signal == "SHORT":
        header     = "🔴 <b>SHORT SIGNAL DETECTED</b>"
        dir_emoji  = "📉"
        entry_icon = "🔴"
        sl_icon    = "🟢"
        tp_icon    = "🎯"
    else:
        header     = "🎯 <b>SIGNAL DETECTED</b>"
        dir_emoji  = "📊"
        entry_icon = "⚪"
        sl_icon    = "🔴"
        tp_icon    = "🎯"

    # 7 điều kiện
    conditions = [
        data.get("cond1", "Market Structure Aligned"),
        data.get("cond2", "Zone Confluence"),
        data.get("cond3", "Rejection Candle"),
        data.get("cond4", "N+1 Candle Confirmed"),
        data.get("cond5", "Session: London/NY"),
        data.get("cond6", "SL/TP Defined"),
        data.get("cond7", f"R:R = {rr}"),
    ]
    conditions_html = "\n".join(f"  ✅ {c}" for c in conditions)

    message = f"""{header}

━━━━━━━━━━━━━━━━━━━━━━━
📊 <b>Pair:</b>      <code>{pair}</code>
🕐 <b>Time:</b>      {time_str}
⏱ <b>Timeframe:</b> {timeframe}
{dir_emoji} <b>Signal:</b>   <b>{signal if signal else "N/A"}</b>
━━━━━━━━━━━━━━━━━━━━━━━

💼 <b>TRADE SETUP</b>
  {entry_icon} Entry:         <code>{entry}</code>
  {sl_icon} Stop Loss:     <code>{stop_loss}</code>
  {tp_icon} Target:        <code>{target}</code>
  ⚖️ R:R Ratio:     <b>{rr}</b>
  📦 Position Size: <b>{pos_size}</b>

━━━━━━━━━━━━━━━━━━━━━━━

✅ <b>CONDITIONS MET</b>
{conditions_html}

━━━━━━━━━━━━━━━━━━━━━━━
📉 <a href="{chart_link}">View Chart on TradingView</a>
"""
    return message.strip()


# ─── Endpoint: POST /webhook ──────────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    """Nhận alert từ TradingView, xác thực, và forward đến Telegram."""
    logger.info(f"📩 Incoming webhook from {request.remote_addr}")

    # 1. Security check
    provided_key = (
        request.args.get("secret")
        or request.headers.get("X-Secret-Key")
        or (request.json or {}).get("secret")
    )
    if SECRET_KEY and provided_key != SECRET_KEY:
        logger.warning("⛔ Unauthorized request — invalid secret key")
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # 2. Parse body
    data = request.json
    if not data:
        logger.warning("⚠️ Empty or non-JSON body received")
        return jsonify({"status": "error", "message": "No JSON body"}), 400

    logger.info(f"📋 Payload: {data}")

    # 3. Format & send
    try:
        message = format_alert_message(data)
        result  = send_telegram_message(message)
        return jsonify({"status": "ok", "telegram_response": result}), 200
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ─── Endpoint: GET /health ────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    """Health check — Railway/uptime monitors gọi endpoint này."""
    return jsonify({
        "status": "ok",
        "service": "TradingView-Telegram Bridge",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "telegram_configured": bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID),
    }), 200


# ─── Endpoint: GET /test ──────────────────────────────────────────────────────
@app.route("/test", methods=["GET"])
def test():
    """Gửi test message đến Telegram để verify kết nối."""
    sample_data = {
        "pair":          "BTCUSDT",
        "time":          datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "timeframe":     "4H",
        "entry":         "65,420.00",
        "stop_loss":     "64,800.00",
        "target":        "66,660.00",
        "rr":            "2.0:1",
        "position_size": "1.5%",
        "chart_link":    "https://www.tradingview.com/chart/?symbol=BINANCE:BTCUSDT",
    }
    try:
        message = format_alert_message(sample_data)
        result  = send_telegram_message(message)
        return jsonify({"status": "ok", "message": "Test sent to Telegram", "telegram_response": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Starting webhook bridge on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
