import requests
import json

base_url = "http://localhost:5000"

try:
    # Try to login first to get a session
    session = requests.Session()
    # Note: We can't easily login without knowing the password or bypass auth for feed if it's open
    # /api/feed is not auth required
    resp = session.get(f"{base_url}/api/feed")
    print(f"Status: {resp.status_code}")
    print(f"Content: {json.dumps(resp.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
