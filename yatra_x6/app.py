from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
import math

load_dotenv()

from modules.itinerary import generate_itinerary
from modules.routing import get_route
from modules.ticketing import generate_ticket_qr
from modules.sos import send_sos_alert
from models.db import db, Ticket

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


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db.init_app(app)


def api_error(message, status_code=400):
    return jsonify({"error": message}), status_code

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/itinerary", methods=["POST"])
def api_itinerary():
    data = request.json
    required = {"destination", "days", "budget", "interests"}
    if not data or not required.issubset(data):
        return api_error("destination, days, budget, and interests are required")
    if not isinstance(data["days"], int) or not 1 <= data["days"] <= 30:
        return api_error("days must be an integer between 1 and 30")
    if not isinstance(data["budget"], (int, float)) or data["budget"] < 0:
        return api_error("budget must be a non-negative number")
    if not isinstance(data["interests"], list):
        return api_error("interests must be a list")
    try:
        plan = generate_itinerary(data["destination"], data["days"], data["budget"], data["interests"])
    except (RuntimeError, ValueError) as exc:
        return api_error(str(exc), 502)
    return jsonify(plan)

@app.route("/api/route", methods=["POST"])
def api_route():
    data = request.json
    if not data or not data.get("start") or not data.get("end"):
        return api_error("start and end coordinates are required")
    if not all(isinstance(value, (int, float)) for point in (data["start"], data["end"]) for value in point):
        return api_error("coordinates must contain numbers")
    if any(len(point) != 2 for point in (data["start"], data["end"])):
        return api_error("coordinates must be [latitude, longitude]")
    try:
        return jsonify(get_route(data["start"], data["end"]))
    except (RuntimeError, ValueError, KeyError) as exc:
        return api_error(str(exc), 502)

@app.route("/api/ticket", methods=["POST"])
def api_ticket():
    data = request.json
    required = {"name", "monument", "date"}
    if not data or not required.issubset(data):
        return api_error("name, monument, and date are required")
    ticket = Ticket(user_name=data["name"], monument=data["monument"], visit_date=data["date"])
    db.session.add(ticket)
    db.session.commit()
    qr_b64 = generate_ticket_qr(ticket.id)
    return jsonify({"ticket_id": ticket.id, "qr_base64": qr_b64})


@app.route("/api/ticket/<ticket_id>/verify", methods=["POST"])
def verify_ticket(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        return api_error("Ticket not found", 404)
    if ticket.is_verified:
        return jsonify({"verified": False, "message": "Ticket was already used"}), 409
    ticket.is_verified = True
    db.session.commit()
    return jsonify({"verified": True, "message": "Ticket verified", "ticket_id": ticket.id})

@app.route("/api/sos", methods=["POST"])
def api_sos():
    data = request.json
    if not data or not all(key in data for key in ("lat", "lng", "user")):
        return api_error("lat, lng, and user are required")
    if not all(isinstance(data[key], (int, float)) and math.isfinite(data[key]) for key in ("lat", "lng")):
        return api_error("lat and lng must be finite numbers")
    if not -90 <= data["lat"] <= 90 or not -180 <= data["lng"] <= 180:
        return api_error("lat or lng is outside the valid range")
    if not isinstance(data["user"], str) or not data["user"].strip():
        return api_error("user must be a non-empty string")
    try:
        sent, details = send_sos_alert(data["lat"], data["lng"])
    except (RuntimeError, ValueError) as exc:
        return api_error(str(exc), 502)
    if not sent:
        return api_error(details, 502)
    return jsonify({"status": "alert sent"})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)