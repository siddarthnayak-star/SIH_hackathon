import os

def send_sos_alert(latitude, longitude):
    """Send an SOS alert with a Google Maps location through a Telegram bot."""
    import os
    import requests

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token:
        return False, "TELEGRAM_BOT_TOKEN is not configured"
    if not chat_id:
        return False, "TELEGRAM_CHAT_ID is not configured"

    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return False, "Invalid GPS coordinates"

    maps_url = f"https://maps.google.com/?q={lat},{lon}"
    message = (
        "🚨 SOS ALERT 🚨\n\n"
        "Emergency assistance may be required.\n\n"
        f"📍 Location:\n{maps_url}\n\n"
        "⚠️ Please respond immediately."
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": False,
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        try:
            result = response.json()
        except ValueError:
            result = {"raw": response.text}

        if response.ok and result.get("ok") is True:
            return True, result

        description = result.get("description") or result.get("error") or str(result)
        return False, description
    except requests.RequestException as exc:
        return False, f"Telegram request failed: {exc}"

