import requests
import time
import json
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

DATA_FILE = "data.json"

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {"tracking": [], "status": {}}

tracking_list = data["tracking"]
status_cache = data["status"]

last_update_id = None

def save():
    with open(DATA_FILE, "w") as f:
        json.dump({
            "tracking": tracking_list,
            "status": status_cache
        }, f)

def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def get_updates():
    global last_update_id
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    res = requests.get(url).json()

    if not res.get("result"):
        return

    for item in res["result"]:
        update_id = item["update_id"]

        if last_update_id is None or update_id > last_update_id:
            last_update_id = update_id

            if "message" in item:
                text = item["message"].get("text", "")

                if text.startswith("/start"):
                    send("🤖 Bot พร้อมแล้ว")

                elif text.startswith("/add"):
                    try:
                        code = text.split(" ")[1]

                        if code not in tracking_list:
                            tracking_list.append(code)
                            save()
                            send(f"✅ เพิ่ม: {code}")
                        else:
                            send("⚠️ มีแล้ว")
                    except:
                        send("❌ ใช้ /add THxxxx")

def track_spx(tracking_no):
    url = "https://spx.co.th/api/v2/fleet_order/tracking/search"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Origin": "https://spx.co.th",
        "Referer": "https://spx.co.th/"
    }

    payload = {"tracking_no": tracking_no}

    try:
        res = requests.post(url, json=payload, headers=headers)
        data = res.json()

        if not data.get("data"):
            return "ยังไม่พบข้อมูล", ""

        tracking_list_data = data["data"].get("tracking_list", [])

        if not tracking_list_data:
            return "ยังไม่อัปเดต", ""

        latest = tracking_list_data[0]
        status = latest.get("status_desc", "")
        time_text = latest.get("time", "")

        return status, time_text

    except:
        return "error", ""

def check_auto():
    for t in tracking_list:
        status, time_text = track_spx(t)

        old = status_cache.get(t)

        if old != status:
            status_cache[t] = status
            save()

            msg = f"📦 {t}\n📍 {status}"
            if time_text:
                msg += f"\n🕒 {time_text}"

            send(msg)

send("🚀 Bot started")

while True:
    try:
        get_updates()
        check_auto()
        time.sleep(10)
    except:
        time.sleep(5)
