# InstantDRS

> Real-time emergency triage and disaster response coordination.

InstantDRS is an emergency response system built to help coordinate triage and disaster relief in real time. It combines Firebase's live data infrastructure with Google's Gemini API for AI-assisted triage decision support.

---

## What It Does

- **Real-time coordination** — Firebase Realtime Database keeps all responders in sync instantly
- **AI triage assistance** — Gemini API helps prioritize cases and suggest response actions
- **Authentication** — Firebase Auth for secure responder login
- **Incident tracking** — log, update, and monitor active emergencies as they unfold

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Auth** | Firebase Authentication |
| **Database** | Firebase Realtime Database |
| **AI / Triage** | Google Gemini API |
| **Backend** | Python (Flask) |
| **Frontend** | HTML, CSS, JavaScript |

---

## Setup

```bash
# Clone
git clone https://github.com/ronaksarda/InstantDRS.git
cd InstantDRS

# Install dependencies
pip install -r requirements.txt

# Configure Firebase
# Add your Firebase config to config.py or .env:
# FIREBASE_API_KEY=...
# FIREBASE_AUTH_DOMAIN=...
# FIREBASE_DATABASE_URL=...
# FIREBASE_PROJECT_ID=...

# Configure Gemini
# GEMINI_API_KEY=...

# Run
python app.py
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `FIREBASE_API_KEY` | Firebase project API key |
| `FIREBASE_AUTH_DOMAIN` | Firebase auth domain |
| `FIREBASE_DATABASE_URL` | Realtime Database URL |
| `FIREBASE_PROJECT_ID` | Firebase project ID |
| `GEMINI_API_KEY` | Google Gemini API key |

---

## Use Case

Designed for scenarios where multiple responders need to coordinate quickly:
- Natural disaster response
- Mass casualty incidents
- Field triage at large events

The Gemini API integration provides AI-assisted decision support to help overwhelmed responders prioritize effectively.

---

## Status

🟡 Active development

---

## License

MIT

---

*Built by [Ronak Sarda](https://github.com/ronaksarda)*
