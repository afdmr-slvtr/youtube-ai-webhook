"""
api/index.py — WhatsApp Webhook untuk Vercel
Vercel pakai serverless functions, entry point harus di folder api/
"""

import os
import json
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client

app = Flask(__name__)

TWILIO_SID   = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
FROM_WA      = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
TO_WA        = os.environ.get("WHATSAPP_TO")
PC_API_URL   = os.environ.get("PC_API_URL", "")

client = Client(TWILIO_SID, TWILIO_TOKEN)


def send_wa(message: str):
    try:
        client.messages.create(from_=FROM_WA, body=message, to=TO_WA)
    except Exception as e:
        print(f"WA error: {e}")


def call_pc(endpoint: str, data: dict = {}) -> dict:
    if not PC_API_URL:
        return {"error": "PC_API_URL not configured"}
    try:
        r = requests.post(
            f"{PC_API_URL}/{endpoint}",
            json=data,
            timeout=10
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


@app.route("/", methods=["GET"])
def index():
    return {"service": "YouTube AI WhatsApp Bot", "status": "running"}, 200


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "service": "YouTube AI WhatsApp Bot"}, 200


@app.route("/webhook", methods=["POST"])
def webhook():
    incoming = request.values.get("Body", "").strip().lower()
    sender   = request.values.get("From", "")

    print(f"WA from {sender}: '{incoming}'")

    resp = MessagingResponse()

    if incoming == "1":
        result = call_pc("approve_all")
        if "error" in result:
            resp.message(f"❌ PC offline: {result['error']}\nPastikan pc_api.py jalan!")
        else:
            resp.message(result.get("message", "✅ Done!"))

    elif incoming == "2":
        result = call_pc("approve_high")
        if "error" in result:
            resp.message(f"❌ PC offline: {result['error']}")
        else:
            resp.message(result.get("message", "✅ Done!"))

    elif incoming == "3":
        call_pc("reject_plan")
        resp.message("🔄 Plan ditolak. Akan generate ulang.")

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
            resp.message("⚠️ PC offline.")
        else:
            resp.message(result.get("message", "📋 Queue OK"))

    elif incoming == "generate":
        result = call_pc("generate_now")
        resp.message(result.get("message", "📝 Generating..."))

    elif incoming == "analyze":
        result = call_pc("analyze_channel")
        resp.message(result.get("message", "🔍 Analyzing..."))

    elif incoming == "help":
        resp.message(
            "🤖 *YouTube AI Bot*\n\n"
            "*Approval:*\n"
            "  *1* ✅ Approve all\n"
            "  *2* 🔥 Approve HIGH only\n"
            "  *3* ❌ Reject plan\n\n"
            "*Info:*\n"
            "  *status* — system status\n"
            "  *queue* — topic queue\n\n"
            "*Actions:*\n"
            "  *generate* — generate prompt now\n"
            "  *analyze* — analyze channel\n"
        )

    else:
        resp.message(
            "🤖 Bot aktif! Kirim *help* untuk commands."
        )

    return str(resp), 200, {"Content-Type": "text/xml"}