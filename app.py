"""
app.py — WhatsApp Webhook Server untuk Railway
Standalone version tanpa dependency ke local files
"""

import os
import json
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client

app = Flask(__name__)

# ─── Config dari Environment Variables ────────────────────
TWILIO_SID   = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
FROM_WA      = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
TO_WA        = os.environ.get("WHATSAPP_TO")
PC_API_URL   = os.environ.get("PC_API_URL")  # URL PC kamu (ngrok sementara)

client = Client(TWILIO_SID, TWILIO_TOKEN)


def send_wa(message: str):
    """Kirim WA balik ke user"""
    try:
        client.messages.create(from_=FROM_WA, body=message, to=TO_WA)
    except Exception as e:
        print(f"WA error: {e}")


def call_pc(endpoint: str, data: dict = {}) -> dict:
    """
    Kirim perintah ke PC kamu via HTTP.
    PC kamu jalan pc_api.py yang listen perintah dari Railway.
    """
    if not PC_API_URL:
        return {"error": "PC_API_URL not set"}
    try:
        r = requests.post(
            f"{PC_API_URL}/{endpoint}",
            json=data,
            timeout=10
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


# ─── Webhook Handler ──────────────────────────────────────

@app.route("/webhook", methods=["POST"])
def webhook():
    incoming = request.values.get("Body", "").strip().lower()
    sender   = request.values.get("From", "")

    print(f"WA from {sender}: '{incoming}'")

    resp = MessagingResponse()

    # ── Content Plan Approval ──────────────────────
    if incoming == "1":
        result = call_pc("approve_all")
        if "error" in result:
            resp.message(f"❌ PC tidak bisa dihubungi: {result['error']}\nPastikan PC kamu nyala dan pc_api.py jalan!")
        else:
            resp.message(result.get("message", "✅ Done!"))

    elif incoming == "2":
        result = call_pc("approve_high")
        if "error" in result:
            resp.message(f"❌ PC tidak bisa dihubungi: {result['error']}")
        else:
            resp.message(result.get("message", "✅ Done!"))

    elif incoming == "3":
        result = call_pc("reject_plan")
        resp.message("🔄 Plan ditolak. Akan generate ulang.")

    # ── Info Commands ──────────────────────────────
    elif incoming == "status":
        result = call_pc("status")
        if "error" in result:
            resp.message(
                "⚠️ *PC Offline*\n\n"
                "PC kamu mungkin sedang mati atau sleep.\n"
                "Pastikan pc_api.py jalan saat PC aktif."
            )
        else:
            resp.message(result.get("message", "📊 Status OK"))

    elif incoming == "queue":
        result = call_pc("queue")
        if "error" in result:
            resp.message("⚠️ PC offline. Tidak bisa ambil data queue.")
        else:
            resp.message(result.get("message", "📋 Queue OK"))

    elif incoming == "generate":
        result = call_pc("generate_now")
        resp.message(result.get("message", "📝 Generating..."))

    elif incoming == "analyze":
        result = call_pc("analyze_channel")
        resp.message(result.get("message", "🔍 Analyzing..."))

    elif incoming == "schedule":
        result = call_pc("schedule")
        if "error" in result:
            resp.message("⚠️ PC offline. Tidak bisa cek jadwal.")
        else:
            resp.message(result.get("message", "📅 Schedule OK"))

    elif incoming in ["start", "start all", "mulai"]:
        result = call_pc("start_services")
        resp.message(result.get("message",
            "⚠️ PC offline. Nyalakan PC dulu baru kirim 'start'!"))
        
    elif incoming in ["jadwal bulan ini", "monthly schedule", "jadwal"]:
        result = call_pc("monthly_schedule")
        resp.message(result.get("message", "📅 Loading..."))

    elif incoming in ["next", "jadwal berikutnya", "next schedule"]:
        result = call_pc("next_schedule")
        resp.message(result.get("message", "📅 Loading..."))

    elif incoming in ["build schedule", "buat jadwal"]:
        result = call_pc("build_schedule")
        resp.message(result.get("message", "📅 Building..."))

    elif incoming in ["research", "riset", "cari topik"]:
        result = call_pc("research_topics")
        resp.message(result.get("message", "🔍 Researching..."))

    elif incoming in ["content plan", "plan", "buat plan"]:
        result = call_pc("content_plan")
        resp.message(result.get("message", "🧠 Planning..."))

    elif incoming in ["skip", "skip today", "lewati"]:
        result = call_pc("skip_today")
        resp.message(result.get("message", "⏭️ Skipped"))

    elif incoming in ["inbox", "cek inbox"]:
        result = call_pc("inbox_status")
        resp.message(result.get("message", "📂 Checking..."))

    elif incoming == "help":
        resp.message(
            "🤖 *YouTube AI Bot*\n\n"
            "*Approval:*\n"
            "  *1* ✅ Approve all\n"
            "  *2* 🔥 Approve HIGH\n"
            "  *3* ❌ Reject plan\n\n"
            "*Info:*\n"
            "  *status*          — system status\n"
            "  *queue*           — topic queue\n"
            "  *inbox*           — cek folder inbox\n"
            "  *jadwal bulan ini*— full schedule\n"
            "  *next*            — jadwal berikutnya\n\n"
            "*Actions:*\n"
            "  *research*        — AI riset topik baru\n"
            "  *content plan*    — buat & approve plan\n"
            "  *build schedule*  — buat jadwal baru\n"
            "  *generate*        — generate prompt now\n"
            "  *analyze*         — analisa channel\n"
            "  *skip*            — skip jadwal hari ini\n"
            "  *start*           — start all services\n"
        )
    else:
        resp.message(
            "🤖 Bot aktif! Kirim *help* untuk commands.\n\n"
            f"_Received: '{incoming}'_"
        )

    return str(resp)


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "service": "YouTube AI WhatsApp Bot"}, 200


@app.route("/", methods=["GET"])
def index():
    return {"service": "YouTube AI Bot", "status": "running"}, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)