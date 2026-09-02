from __future__ import annotations
import os
import requests

def send_to_telegram(text: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID manquants")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # Telegram limite 4096 chars
    msg = text[:3900]
    r = requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    r.raise_for_status()
