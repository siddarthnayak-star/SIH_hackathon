from flask_sqlalchemy import SQLAlchemy
import uuid

db = SQLAlchemy()

class Ticket(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_name = db.Column(db.String)
    monument = db.Column(db.String)
    visit_date = db.Column(db.String)
    is_verified = db.Column(db.Boolean, default=False)