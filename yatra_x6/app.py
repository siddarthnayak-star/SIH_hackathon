from flask import Flask, request, jsonify, render_template
from modules.itinerary import generate_itinerary
from modules.routing import get_route
from modules.ticketing import generate_ticket_qr
from modules.sos import send_sos_alert
from models.db import db, Ticket

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db.init_app(app)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/itinerary", methods=["POST"])
def api_itinerary():
    data = request.json
    plan = generate_itinerary(data["destination"], data["days"], data["budget"], data["interests"])
    return jsonify(plan)

@app.route("/api/route", methods=["POST"])
def api_route():
    data = request.json
    return jsonify(get_route(data["start"], data["end"]))

@app.route("/api/ticket", methods=["POST"])
def api_ticket():
    data = request.json
    ticket = Ticket(user_name=data["name"], monument=data["monument"], visit_date=data["date"])
    db.session.add(ticket)
    db.session.commit()
    qr_b64 = generate_ticket_qr(ticket.id)
    return jsonify({"ticket_id": ticket.id, "qr_base64": qr_b64})

@app.route("/api/sos", methods=["POST"])
def api_sos():
    data = request.json
    send_sos_alert(data["lat"], data["lng"], data["user"])
    return jsonify({"status": "alert sent"})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)