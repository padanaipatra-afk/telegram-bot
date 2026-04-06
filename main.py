import requests
import time
import json
import os

TELEGRAM_TOKEN = "8712877674:AAF_PkXmkVlQPSaB-vtZAjea2IxGofZohUw"
CHAT_ID = "532790110"

DATA_FILE = "data.json"

# โหลดข้อมูล
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

def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# 🔥 ดึงข้อมูลจาก Shopee (SPX)
def track_spx(tracking):
    try:
        url = f"https://spx.co.th/api/v2/fleet_order/tracking/search?q={tracking}"
        res = requests.get(url).json()

        data = res.get("data", {})
        tracking_list_data = data.get("tracking_list", [])

        if not tracking_list_data:
            return "ยังไม่อัปเดต", ""

        latest = tracking_list_data[0]
        status = latest.get("status_desc", "")
        time_text = latest.get("time", "")

        return status, time_text
    except:
        return "error", ""

# รับข้อความ
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
                text = item["message"].get("text", "")

                if text.startswith("/add"):
                    code = text.replace("/add", "").strip()
                    if code not in tracking_list:
                        tracking_list.append(code)
                        save()
                        send(f"✅ เพิ่มแล้ว {code}")
                    else:
                        send("❗ มีแล้ว")

                elif text.startswith("/check"):
                    for t in tracking_list:
                        status, time_text = track_spx(t)
                        send(f"{t}\n📍 {status}\n⏰ {time_text}")

# 🔥 เช็คอัตโนมัติ
def auto_check():
    for t in tracking_list:
        status, time_text = track_spx(t)

        old = status_cache.get(t)

        # ถ้าสถานะเปลี่ยน → แจ้ง
        if old != status:
            status_cache[t] = status
            save()

            msg = f"📦 {t}\n📍 {status}"
            if time_text:
                msg += f"\n⏰ {time_text}"

            send(msg)

# เริ่มทำงาน
send("🚀 Bot started")

while True:
    try:
        get_updates()
        auto_check()
        time.sleep(30)  # 🔥 เช็คทุก 30 วินาที
    except Exception as e:
        send(f"❌ error: {e}")
        time.sleep(10)
