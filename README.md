# Crowd Monitoring System for Malls (Minimal Working Project)

**What this package contains**
- A minimal Flask-based web app with Admin and User roles.
- User dashboard includes a simple rule-based AI chatbot (text + Web Speech API),
  parking dashboard (6 slots) that updates in real-time via Socket.IO,
  and a mall crowd panel that displays counts reported by the admin.
- Admin dashboard can toggle parking slots and upload a video file. Video processing
  is implemented as a placeholder (a simple face detector if OpenCV and models are present).

**Important**
- This is a *starter/full-stack template* demonstrating how to wire together:
  Flask + Flask-SocketIO, HTML/JS frontend with Web Speech API, parking slot management,
  simple video-upload plumbing, and real-time updates.
- **Age estimation and robust people entry/exit tracking require pre-trained ML models**
  (not included). Places to drop models and instructions are in `app.py` and `utils/video_processing.py`.

**How to run (Linux / macOS / WSL)**
1. Create a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python app.py
   ```
4. Open http://localhost:5000 in your browser.

**Default users**
- Admin: username `admin`, password `adminpass`
- User: username `user`, password `userpass`

**Notes / Next steps to improve**
- Add real age-estimation models (e.g., DeepFace, wide-resnet based models) and place model files in `models/`.
- Implement proper production authentication (Flask-Login + database).
- Use Redis or database for persistence and horizontal scaling.
- For a production voice chatbot connect to an LLM or embedding-based QA backend.
