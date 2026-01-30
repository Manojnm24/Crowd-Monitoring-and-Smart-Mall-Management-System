from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import cv2
import numpy as np
import os
import base64
from collections import OrderedDict
from scipy.spatial import distance as dist
from collections import deque
import requests
import os

# ------------------ GEMINI CONFIG ------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
USE_GEMINI = False   # Set True only when key is available

if USE_GEMINI and GEMINI_API_KEY:
    GEMINI_URL = (
        "https://generativelanguage.googleapis.com/v1/models/"
        "gemini-1.0-pro:generateContent?key=" + GEMINI_API_KEY
    )
else:
    GEMINI_URL = None
# 🔒 Store last few age predictions (for webcam only)
age_history = deque(maxlen=7)

# ------------------ WEBCAM GLOBAL STATE ------------------
frame_counter = 0                 # for frame skipping
FACE_PROCESS_EVERY_N_FRAMES = 3   # adjust: 2 = faster, 3 = stable, 4 = more speed

last_face_results = []            # cache last good age/gender

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Use an environment variable in production
socketio = SocketIO(app, cors_allowed_origins="*")

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ------------------ MODEL PATHS ------------------
ROOT = os.getcwd()
MODEL_DIR = os.path.join(ROOT, 'models')

FACE_CASCADE_PATH = os.path.join(MODEL_DIR, 'haarcascade_frontalface_default.xml')
AGE_PROTO = os.path.join(MODEL_DIR, "age_deploy.prototxt")
AGE_MODEL = os.path.join(MODEL_DIR, "age_net.caffemodel")
GENDER_PROTO = os.path.join(MODEL_DIR, "gender_deploy.prototxt")
GENDER_MODEL = os.path.join(MODEL_DIR, "gender_net.caffemodel")

# ------------------ CHECK MODELS EXIST ------------------
def check_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required file not found: {path}")

for p in [FACE_CASCADE_PATH, AGE_PROTO, AGE_MODEL, GENDER_PROTO, GENDER_MODEL]:
    check_file(p)

# ------------------ LOAD MODELS ------------------
face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
if face_cascade.empty():
    raise RuntimeError("Failed to load Haar cascade. Check path: " + FACE_CASCADE_PATH)

age_net = cv2.dnn.readNetFromCaffe(AGE_PROTO, AGE_MODEL)
gender_net = cv2.dnn.readNetFromCaffe(GENDER_PROTO, GENDER_MODEL)

AGE_LIST = ['(0-2)', '(4-6)', '(8-12)', '(15-20)',
            '(25-32)', '(38-43)', '(48-53)', '(60-100)']

GENDER_LIST = ['Male', 'Female']

AGE_MEAN = (78.4263377603, 87.7689143744, 114.895847746)


# ✅ FIXED 5-YEAR AGE GROUP MAPPING
def age_band_to_5yr_group(age_range):
    mapping = {
        "(0-2)": "0-5",
        "(4-6)": "5-10",
        "(8-12)": "10-15",
        "(15-20)": "15-20",
        "(25-32)": "20-25",
        "(38-43)": "35-40",
        "(48-53)": "45-50",
        "(60-100)": "60+"
    }
    return mapping.get(age_range, "Unknown")


# ------------------ STATE ------------------
state = {
    "mall": {"in": 0, "out": 0, "inside": 0},
    "parking": {"A1": "free", "A2": "booked", "A3": "free","A4": "free", "A5": "booked", "A6": "free"}
}

UPLOAD_DIR = os.path.join(ROOT, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ------------------ SIMPLE CENTROID TRACKER ------------------
class CentroidTracker:
    def __init__(self, maxDisappeared=40):  # Fixed: was _init_
        self.nextObjectID = 0
        self.objects = OrderedDict()   # id -> centroid (x,y)
        self.disappeared = OrderedDict()
        self.maxDisappeared = maxDisappeared

    def register(self, centroid):
        self.objects[self.nextObjectID] = centroid
        self.disappeared[self.nextObjectID] = 0
        self.nextObjectID += 1

    def deregister(self, objectID):
        if objectID in self.objects:
            del self.objects[objectID]
        if objectID in self.disappeared:
            del self.disappeared[objectID]

    def update(self, rects):
        # rects: list of (x1,y1,x2,y2)
        if len(rects) == 0:
            # mark all as disappeared
            for objectID in list(self.disappeared.keys()):
                self.disappeared[objectID] += 1
                if self.disappeared[objectID] > self.maxDisappeared:
                    self.deregister(objectID)
            return self.objects

        inputCentroids = []
        for (x1,y1,x2,y2) in rects:
            cX = int((x1 + x2) / 2.0)
            cY = int((y1 + y2) / 2.0)
            inputCentroids.append((cX, cY))

        if len(self.objects) == 0:
            for c in inputCentroids:
                self.register(c)
        else:
            objectIDs = list(self.objects.keys())
            objectCentroids = list(self.objects.values())

            D = dist.cdist(np.array(objectCentroids), np.array(inputCentroids))
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            usedRows = set()
            usedCols = set()

            for (r, c) in zip(rows, cols):
                if r in usedRows or c in usedCols:
                    continue
                objectID = objectIDs[r]
                self.objects[objectID] = inputCentroids[c]
                self.disappeared[objectID] = 0
                usedRows.add(r)
                usedCols.add(c)

            unusedRows = set(range(0, D.shape[0])) - usedRows
            unusedCols = set(range(0, D.shape[1])) - usedCols

            # disappeared objects
            for r in unusedRows:
                objectID = objectIDs[r]
                self.disappeared[objectID] += 1
                if self.disappeared[objectID] > self.maxDisappeared:
                    self.deregister(objectID)

            # new objects
            for c in unusedCols:
                self.register(inputCentroids[c])

        return self.objects

# ------------------ USER MODEL FOR FLASK-LOGIN ------------------
class User(UserMixin):
    def __init__(self, id, username, password, is_admin=False):
        self.id = id
        self.username = username
        self.password = password
        self.is_admin = is_admin

# Hardcoded users for demo (replace with DB in production)
users = {
    'admin': User('admin', 'admin', 'admin123', is_admin=True),
    'user': User('user', 'user', 'user123', is_admin=False)
}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

# ------------------ ROUTES ------------------
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)
        if user and user.password == password:
            login_user(user)
            if user.is_admin:
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('user'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for('user'))
    return render_template('admin.html')

@app.route('/user')
@login_required
def user():
    return render_template('user.html')

# ------------------ API: GET STATE ------------------
@app.route('/api/get_state')
@login_required
def get_state():
    return jsonify(state)

# ------------------ TOGGLE PARKING (Admin only) ------------------
@app.route('/api/toggle_parking', methods=['POST'])
@login_required
def toggle_parking():
    if not current_user.is_admin:
        return jsonify(success=False, message="Admin access required"), 403
    data = request.get_json()
    slot = data.get('slot')
    if slot not in state['parking']:
        return jsonify(success=False, message="Invalid slot"), 400
    state['parking'][slot] = 'free' if state['parking'][slot] == 'booked' else 'booked'
    socketio.emit('parking_update', state['parking'])
    return jsonify(success=True, state=state['parking'])

# ------------------ HELPERS: AGE/GENDER PREDICT ------------------





# ------------------ UPLOAD VIDEO (Admin only) ------------------
# ------------------ UPLOAD VIDEO (Admin only) ------------------
MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
age_list = ["(0-2)", "(4-6)", "(8-12)", "(15-20)", "(25-32)", "(38-43)", "(48-53)", "(60-100)"]
gender_list = ["Male", "Female"]

from ultralytics import YOLO

yolo_model = YOLO("yolov8n.pt")  # person detector

@app.route('/api/upload_video', methods=['POST'])
@login_required
def upload_video():
    if not current_user.is_admin:
        return jsonify(success=False, message="Admin access required"), 403

    file = request.files.get('file')
    if not file:
        return jsonify(success=False, message="No file provided"), 400

    filepath = os.path.join(UPLOAD_DIR, file.filename)
    file.save(filepath)

    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        return jsonify(success=False, message="Failed to open video"), 400

    tracker = CentroidTracker(maxDisappeared=40)

    prev_positions = {}
    counted_out = set()
    out_count = 0

    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
    zone_top = frame_height - 100
    zone_bottom = frame_height - 20

    frame_no = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_no += 1
        if frame_no % 2 != 0:
            continue

        rects = []

        # -------- YOLO PERSON DETECTION --------
        results = yolo_model(frame, conf=0.5, iou=0.45, verbose=False)
        for r in results:
            for box in r.boxes:
                if int(box.cls[0]) == 0:  # PERSON
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    rects.append((x1, y1, x2, y2))
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        objects = tracker.update(rects)
        inside = len(objects)

        # -------- POSITION TRACKING --------
        for objectID, (cX, cY) in objects.items():
            prev = prev_positions.get(objectID)

            if cY < zone_top:
                pos = "above"
            elif cY > zone_bottom:
                pos = "below"
            else:
                pos = prev

            prev_positions[objectID] = pos
            cv2.circle(frame, (cX, cY), 4, (0, 0, 255), -1)

        # -------- EXIT COUNT (WHEN DISAPPEARS) --------
        current_ids = set(objects.keys())
        for oid in list(prev_positions.keys()):
            if oid not in current_ids:
                if prev_positions[oid] == "above" and oid not in counted_out:
                    out_count += 1
                    counted_out.add(oid)
                prev_positions.pop(oid)

        total_crowd = inside + out_count

        # -------- DRAW UI --------
        cv2.rectangle(frame, (0, zone_top),
                      (frame.shape[1], zone_bottom), (0, 255, 255), 2)

        cv2.putText(frame, f"TOTAL CROWD: {total_crowd}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(frame, f"EXITED: {out_count}", (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame, f"CURRENT INSIDE: {inside}", (20, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("YOLOv8 Crowd Counting", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    state['mall']['inside'] = inside
    state['mall']['out'] = out_count
    state['mall']['in'] = total_crowd

    socketio.emit('mall_update', state['mall'])
    return jsonify(success=True, result=state['mall'])

# ------------------ UPLOAD PHOTO (NEW FIXED VERSION) ------------------
@app.route("/api/upload_photo", methods=["POST"])
@login_required
def upload_photo():

    file = request.files.get("file")
    if not file:
        return jsonify(success=False, message="No photo uploaded"), 400

    image_path = os.path.join(UPLOAD_DIR, file.filename)
    file.save(image_path)

    img = cv2.imread(image_path)
    if img is None:
        return jsonify(success=False, message="Invalid image"), 400

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.2, 5)

    results = []

    for (x, y, w, h) in faces:
        if w < 40 or h < 40:
            continue

        face = img[y:y+h, x:x+w]

        blob = cv2.dnn.blobFromImage(
            face,
            1.0,
            (227, 227),
            AGE_MEAN,
            swapRB=False
        )

        # Gender prediction
        gender_net.setInput(blob)
        gender_preds = gender_net.forward()
        gender = GENDER_LIST[gender_preds[0].argmax()]

        # Age prediction
        age_net.setInput(blob)
        age_preds = age_net.forward()
        age_range = AGE_LIST[age_preds[0].argmax()]

        # ✅ Convert to correct 5-year band
        age_group = age_band_to_5yr_group(age_range)

        results.append({
            "age": age_group,
            "gender": gender
        })

    return jsonify(success=True, result=results)


# ------------------ DETECT AGE & GENDER ------------------


# ------------------ WEBCAM STREAM (socket) ------------------
# ------------------ WEBCAM STREAM (socket) ------------------
# -------- WEBCAM OPTIMIZATION --------
WEBCAM_FRAME_SKIP = 8        # run age/gender once every 5 frames
webcam_frame_count = 0
last_face_results = []      # cache results
# -------- ACCURATE FACE CACHE --------
face_cache = {}   # key: (x,y,w,h) approx → {age, gender}

@socketio.on('webcam_frame')
def handle_webcam_frame(data):
    global frame_counter, last_face_results

    try:
        frame_counter += 1

        # 🚀 SPEED CONTROL (process only every Nth frame)
        if frame_counter % FACE_PROCESS_EVERY_N_FRAMES != 0:
            emit('face_data', last_face_results)
            return

        # ---------- Decode image ----------
        if ',' in data:
            img_data = base64.b64decode(data.split(',')[1])
        else:
            img_data = base64.b64decode(data)

        img_array = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if frame is None:
            emit('face_data', last_face_results)
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # ---------- FACE DETECTION ----------
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(80, 80)   # ❗ important for accuracy
        )

        results = []

        for (x, y, w, h) in faces:
            face = frame[y:y+h, x:x+w]

            # ---------- PREPROCESS ----------
            blob = cv2.dnn.blobFromImage(
                face,
                1.0,
                (227, 227),
                AGE_MEAN,
                swapRB=False
            )

            # ---------- GENDER ----------
            gender_net.setInput(blob)
            gender_preds = gender_net.forward()
            gender = GENDER_LIST[gender_preds[0].argmax()]

            # ---------- AGE ----------
            age_net.setInput(blob)
            age_preds = age_net.forward()
            age_range = AGE_LIST[age_preds[0].argmax()]
            age_group = age_band_to_5yr_group(age_range)

            results.append({
                "x": int(x),
                "y": int(y),
                "w": int(w),
                "h": int(h),
                "gender": gender,
                "age": age_group
            })

        # ---------- CACHE RESULTS ----------
        if results:
            last_face_results = results

        emit('face_data', last_face_results)

    except Exception as e:
        print("webcam_frame error:", e)
        emit('face_data', last_face_results)



# ------------------ CHATBOT (ChatGPT) ------------------


@app.route("/api/chat", methods=["POST"])
@login_required
def chat_with_ai():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    mall = state["mall"]
    parking = state["parking"]

    prompt = f"""
You are a Smart Mall Assistant.

Live mall information:
- Total entered: {mall['in']}
- Currently inside: {mall['inside']}
- Exited: {mall['out']}

Parking slots:
{parking}

User question:
{user_message}
"""

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        response = requests.post(
            GEMINI_URL,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            print("Gemini error:", response.text)
            return jsonify(reply="AI service error")

        reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return jsonify(reply=reply)

    except Exception as e:
        print("Gemini exception:", e)
        return jsonify(reply="AI service unavailable")

       
# ------------------ SOCKET: SEND INITIAL DATA TO USER ------------------
# ------------------ SOCKET: SEND INITIAL DATA TO USER ------------------
@socketio.on('connect')
def handle_connect():
    """Send current mall and parking data to user on page load."""
    try:
        emit('full_state', {
            'parking': state['parking'],
            'mall': state['mall']  # includes in, out, inside, age/gender if available
        })
        print("Initial state sent to connected client.")
    except Exception as e:
        print("Socket connect error:", e)



# ------------------ MAIN ------------------
if __name__ == '__main__':
    # set debug True for dev only
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)