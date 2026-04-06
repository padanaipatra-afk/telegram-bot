import requests
import time
import os
from flask import Flask
from threading import Thread

# ================== CONFIG ==================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = None  # ไม่ต้องใช้แล้ว

DATA_FILE = "data.json"

# ================== WEB (กัน Render ดับ) ==================
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# ================== LOAD DATA ==================
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {"tracking": [], "status": {}}

tracking_list = data["tracking"]
status_cache = data["status"]

def save():
    with open(DATA_FILE, "w") as f:
        json.dump({
            "tracking": tracking_list,
            "status": status_cache
        }, f)

# ================== TELEGRAM ==================
def send(chat_id, msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": msg})

last_update_id = None

def get_updates():
    global last_update_id

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    res = requests.get(url).json()

    for item in res["result"]:
        update_id = item["update_id"]

        if last_update_id is None or update_id > last_update_id:
            last_update_id = update_id

            if "message" in item:
                chat_id = item["message"]["chat"]["id"]
                text = item["message"].get("text", "")

                handle_command(chat_id, text)

# ================== SHOPEE TRACK ==================
def track_spx(tracking):
    try:
        url = f"https://spx.co.th/api/v2/fleet_order/tracking/search?q={tracking}"
        res = requests.get(url).json()

        orders = res.get("data", {}).get("orders", [])
        if not orders:
            return "ไม่พบพัสดุ", ""

        latest = orders[0].get("latest_status", {})
        status = latest.get("status", "ไม่ทราบสถานะ")
        time_text = latest.get("timestamp", "")

        return status, time_text

    except:
        return "error", ""

# ================== COMMAND ==================
def handle_command(chat_id, text):
    if text == "/start":
        send(chat_id, "🚀 Bot Shopee พร้อมแล้ว\nใช้ /add เลขพัสดุ")

    elif text.startswith("/add"):
        parts = text.split()
        if len(parts) < 2:
            send(chat_id, "❌ ใส่เลขพัสดุด้วย")
            return

        tracking = parts[1]

        if tracking not in tracking_list:
            tracking_list.append(tracking)
            save()
            send(chat_id, f"✅ เพิ่มแล้ว {tracking}")
        else:
            send(chat_id, "📦 มีอยู่แล้ว")

    elif text.startswith("/check"):
        if not tracking_list:
            send(chat_id, "❌ ไม่มีพัสดุ")
            return

        for t in tracking_list:
            status, time_text = track_spx(t)

            msg = f"📦 {t}\n📍 {status}"
            if time_text:
                msg += f"\n⏰ {time_text}"

            send(chat_id, msg)

# ================== AUTO CHECK ==================
def check_auto():
    for t in tracking_list:
        status, time_text = track_spx(t)

        old = status_cache.get(t)

        if old != status:
            status_cache[t] = status
            save()

            msg = f"📦 {t}\n📍 {status}"
            if time_text:
                msg += f"\n⏰ {time_text}"

            send( tracking_list_chat_id, msg)

# ================== MAIN ==================
keep_alive()

print("🚀 Bot started")

while True:
    try:
        get_updates()
        time.sleep(10)
    except:
        time.sleep(5)
