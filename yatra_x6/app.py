from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template

load_dotenv()

from modules.itinerary import generate_itinerary
from modules.routing import get_route
from modules.ticketing import generate_ticket_qr
from modules.sos import send_sos_alert
from models.db import db, Ticket

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
    try:
        send_sos_alert(data["lat"], data["lng"], data["user"])
    except (RuntimeError, ValueError) as exc:
        return api_error(str(exc), 502)
    return jsonify({"status": "alert sent"})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)