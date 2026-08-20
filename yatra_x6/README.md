# Yatra X6

AI-powered smart tourism platform for SIH 2026.

## Features

- Gemini-powered day-by-day itinerary planning
- OpenRouteService routing with a Leaflet map
- SQLite ticket storage with QR generation and one-time verification
- Browser geolocation SOS alerts through Twilio

## Local setup

From the `yatra_x6` directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill the values in `.env` before testing provider-backed features:

```text
GEMINI_API_KEY=your-gemini-key
ORS_API_KEY=your-openrouteservice-key
TWILIO_SID=your-twilio-sid
TWILIO_AUTH=your-twilio-auth-token
TWILIO_FROM=your-twilio-number
EMERGENCY_CONTACT_NUMBER=destination-number
```

Never commit `.env` or API keys.

## Run

```powershell
python app.py
```

Open <http://127.0.0.1:5000> in a browser. Camera and geolocation features require a secure context such as localhost or HTTPS.

## API smoke checks

The frontend uses these routes:

- `POST /api/itinerary`
- `POST /api/route`
- `POST /api/ticket`
- `POST /api/ticket/<ticket_id>/verify`
- `POST /api/sos`

The QR scanner sends the decoded ticket ID to the verification route. A ticket can be verified only once; a second attempt returns HTTP `409`.

## Team workflow

Work on feature branches and open a pull request into `main`. Keep provider keys in local environment variables and do not commit generated files, virtual environments, or the SQLite database.
