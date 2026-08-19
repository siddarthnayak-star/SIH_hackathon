from twilio.rest import Client
import os

def send_sos_alert(lat, lng, user_name):
    required = ("TWILIO_SID", "TWILIO_AUTH", "TWILIO_FROM", "EMERGENCY_CONTACT_NUMBER")
    if any(not os.getenv(key) for key in required):
        raise ValueError("Twilio SOS environment variables are not configured.")
    client = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_AUTH"))
    maps_link = f"https://maps.google.com/?q={lat},{lng}"
    client.messages.create(
        body=f"SOS from {user_name}. Location: {maps_link}",
        from_=os.getenv("TWILIO_FROM"),
        to=os.getenv("EMERGENCY_CONTACT_NUMBER")
    )