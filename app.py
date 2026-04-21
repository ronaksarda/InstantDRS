import os
import json
import subprocess
import time
import base64
import re
from functools import wraps
from flask import Flask, request, jsonify, render_template, Response, session, redirect
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "instantdrs-secret-2026")
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CPP_BINARY = "priority_engine.exe" if os.name == 'nt' else "./priority_engine"
QUEUE_FILE = os.path.join(os.path.dirname(__file__), "live_queue.json")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")
AUTHORITY_PIN = os.getenv("AUTHORITY_PIN", "1234")
os.makedirs(UPLOAD_DIR, exist_ok=True)

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_CRED_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if FIREBASE_CRED_PATH and os.path.exists(FIREBASE_CRED_PATH):
        cred = credentials.Certificate(FIREBASE_CRED_PATH)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
    else:
        db = None
except Exception:
    db = None

def load_queue():
    if db:
        try:
            doc = db.collection('dispatches').document('live_queue').get()
            if doc.exists:
                return doc.to_dict()
        except Exception as e:
            print(f"FIRESTORE LOAD ERROR: {e}")
    # Fallback to local
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            pass
    return {"incidents": [], "stats": {"total_received": 0, "avg_severity": 0}}

def save_queue(data):
    if db:
        try:
            db.collection('dispatches').document('live_queue').set(data)
        except Exception as e:
            print(f"FIRESTORE SAVE ERROR: {e}")
    # Always save local fallback
    with open(QUEUE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def sanitize(text, max_len=500):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', str(text))
    return text[:max_len].strip()

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authority_auth'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

GEMINI_SYSTEM_PROMPT = """You are InstantDRS, a high-precision AI emergency dispatch triage agent.

OBJECTIVE:
Analyze emergency reports (text + image) to provide immediate, actionable triage data for first responders.

OUTPUT JSON SCHEMA:
{
  "severity": <int 1-10, 10=IMMINENT LIFE THREAT>,
  "type": "Fire | Medical | Violence | Flood | Accident | Other",
  "verified": <bool, true if image matches report>,
  "summary": "<string, max 15 words tactical summary>",
  "recommended_units": "<string, e.g. 2 Engines + 1 ALS Ambulance>",
  "secondary_risks": "<string, hazards like 'Gas leak' or 'Crowd control needed'>",
  "ai_reasoning": "<string, short clinical explanation for the score>"
}"""

def analyze_emergency(text, img_b64, emergency_type):
    if not client:
        return fallback_analysis(text, emergency_type, img_b64)
    
    try:
        user_msg = f"Emergency Type: {emergency_type}\nVictim Report: {text}"
        contents = [GEMINI_SYSTEM_PROMPT + "\n\n" + user_msg]
        
        if img_b64:
            contents.append(types.Part.from_bytes(
                data=base64.b64decode(img_b64),
                mime_type="image/jpeg"
            ))
            
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=contents
        )
        
        text_resp = response.text.strip().replace('```json', '').replace('```', '').strip()
        return json.loads(text_resp)
    except Exception as e:
        print(f"GEMINI ERROR: {e}")
        return fallback_analysis(text, emergency_type, img_b64)

def fallback_analysis(text, emergency_type, img_b64):
    severity_map = {"Fire": 9, "Medical": 8, "Violence": 10, "Natural Disaster": 9, "Accident": 7, "Flood": 8, "Other": 5}
    return {
        "severity": severity_map.get(emergency_type, 5),
        "type": emergency_type,
        "verified": bool(img_b64),
        "summary": text[:60] if text else "No description",
        "recommended_units": "Standard Response",
        "secondary_risks": "Unknown"
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/authority')
@auth_required
def authority():
    return render_template('authority.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()
        # Hardcoded for hackathon, in production use Firebase Auth or secure DB
        admin_pass = os.getenv("ADMIN_PASSWORD", "InstantDRS2026")
        if username == 'admin' and password == admin_pass:
            session['authority_auth'] = True
            session['username'] = username
            return redirect('/authority')
        return render_template('login.html', error=True)
    return render_template('login.html', error=False)

@app.route('/logout')
def logout():
    session.pop('authority_auth', None)
    return redirect('/login')

@app.route('/submitted.html')
def submitted():
    return render_template('submitted.html')

@app.route('/triage', methods=['POST'])
def triage():
    data = request.json
    if not data:
        return jsonify({"error": "No data"}), 400

    text = sanitize(data.get('text', ''))
    emergency_type = sanitize(data.get('emergency_type', 'Other'), 30)
    if not text or not emergency_type:
        return jsonify({"error": "Missing required fields"}), 400

    analysis = analyze_emergency(text, data.get('image_b64'), emergency_type)

    user_severity = data.get('severity')
    incident_id = f"SOS_{int(time.time())}_{str(time.time()).split('.')[-1][:4]}"

    image_url = ''
    if data.get('image_b64'):
        try:
            img_data = base64.b64decode(data['image_b64'])
            img_filename = f"{incident_id}.jpg"
            with open(os.path.join(UPLOAD_DIR, img_filename), 'wb') as f:
                f.write(img_data)
            image_url = f"/static/uploads/{img_filename}"
        except Exception:
            pass

    audio_url = ''
    if data.get('audio_b64'):
        try:
            audio_data = base64.b64decode(data['audio_b64'])
            audio_filename = f"{incident_id}.webm"
            with open(os.path.join(UPLOAD_DIR, audio_filename), 'wb') as f:
                f.write(audio_data)
            audio_url = f"/static/uploads/{audio_filename}"
        except Exception:
            pass

    video_url = ''
    if data.get('video_b64'):
        try:
            video_data = base64.b64decode(data['video_b64'])
            video_filename = f"{incident_id}.mp4"
            with open(os.path.join(UPLOAD_DIR, video_filename), 'wb') as f:
                f.write(video_data)
            video_url = f"/static/uploads/{video_filename}"
        except Exception:
            pass

    report = {
        "id": incident_id,
        "severity": max(1, min(10, int(user_severity))) if user_severity else analysis.get('severity', 5),
        "type": emergency_type,
        "verified": analysis.get('verified', False),
        "summary": sanitize(analysis.get('summary', text[:60]), 120),
        "recommended_units": analysis.get('recommended_units', 'Standard Response'),
        "secondary_risks": analysis.get('secondary_risks', 'None'),
        "ai_reasoning": analysis.get('ai_reasoning', 'Manual triage required'),
        "time": int(time.time()),
        "lat": float(data.get('lat', 0.0)),
        "lng": float(data.get('lng', 0.0)),
        "text": text,
        "location_text": sanitize(data.get('location_text', ''), 200),
        "has_image": bool(data.get('image_b64')),
        "image_url": image_url,
        "has_audio": bool(data.get('audio_b64')),
        "audio_url": audio_url,
        "has_video": bool(data.get('video_b64')),
        "video_url": video_url,
        "status": "active"
    }

    current_state = load_queue()
    
    # Send only necessary primitive fields to C++ to avoid parser breakage on complex string data
    cpp_incidents = [{"id": inc["id"], "severity": inc["severity"], "time": inc["time"]} for inc in current_state.get("incidents", []) if "id" in inc]
    cpp_new = {"id": report["id"], "severity": report["severity"], "time": report["time"]}
    cpp_input = {"incidents": cpp_incidents, "new": cpp_new}

    cpp_used = False
    cpp_time_ms = 0
    try:
        t0 = time.time()
        process = subprocess.Popen([CPP_BINARY], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate(input=json.dumps(cpp_input), timeout=5)
        cpp_time_ms = round((time.time() - t0) * 1000, 1)
        cpp_out = json.loads(stdout)
        sorted_ids = cpp_out.get("sorted_ids", [])
        all_incidents = current_state.get("incidents", []) + [report]
        inc_map = {inc['id']: inc for inc in all_incidents}
        sorted_list = [inc_map[sid] for sid in sorted_ids if sid in inc_map]
        cpp_used = True
        print(f"C++ ENGINE: sorted {len(sorted_ids)} incidents in {cpp_time_ms}ms")
    except Exception as e:
        print(f"BRIDGE ERROR: {e}")
        sorted_list = [report] + current_state.get("incidents", [])

    total_received = current_state.get("stats", {}).get("total_received", 0) + 1
    all_sevs = [inc.get('severity', 0) for inc in sorted_list]
    avg_sev = round(sum(all_sevs) / len(all_sevs), 1) if all_sevs else 0

    queue_data = {
        "incidents": sorted_list,
        "last_update": int(time.time()),
        "stats": {
            "total_received": total_received,
            "avg_severity": avg_sev,
            "active_count": len(sorted_list),
            "critical_count": sum(1 for s in all_sevs if s >= 9)
        }
    }
    save_queue(queue_data)

    # Firebase sync is now handled inside save_queue


    return jsonify({
        "status": "triaged",
        "id": incident_id,
        "cpp_engine": cpp_used,
        "cpp_time_ms": cpp_time_ms,
        "queue_size": len(sorted_list),
        "ai_analysis": {
            "summary": analysis.get('summary', ''),
            "recommended_units": analysis.get('recommended_units', ''),
            "secondary_risks": analysis.get('secondary_risks', ''),
            "ai_reasoning": analysis.get('ai_reasoning', '')
        }
    }), 200

@app.route('/api/feed')
def api_feed():
    return jsonify(load_queue())

@app.route('/api/resolve', methods=['POST'])
@auth_required
def resolve_incident():
    data = request.json
    incident_id = data.get('id')
    if not incident_id:
        return jsonify({"error": "No ID"}), 400
    
    queue = load_queue()
    # Find the incident to store full data
    incident = next((inc for inc in queue.get('incidents', []) if inc['id'] == incident_id), None)
    
    if incident:
        incident['status'] = 'resolved'
        incident['resolved_at'] = int(time.time())
        # Remove from active incidents
        queue['incidents'] = [inc for inc in queue['incidents'] if inc['id'] != incident_id]
        
        resolved = queue.get('resolved', [])
        resolved.append(incident)
        # Keep only last 50 resolved cases
        queue['resolved'] = resolved[-50:]
        queue['last_update'] = int(time.time())
        # Update active count in stats
        if 'stats' in queue:
            queue['stats']['active_count'] = len(queue['incidents'])
        save_queue(queue)
        return jsonify({"status": "resolved"}), 200
    
    return jsonify({"error": "Incident not found"}), 404

@app.route('/api/stream')
def stream():
    def event_stream():
        last_update = 0
        while True:
            data = load_queue()
            current_update = data.get("last_update", 0)
            if current_update != last_update:
                last_update = current_update
                yield f"data: {json.dumps(data)}\n\n"
            time.sleep(1)
    return Response(event_stream(), mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
