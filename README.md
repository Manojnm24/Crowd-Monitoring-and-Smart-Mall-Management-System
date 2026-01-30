# Crowd Monitoring System for Malls 🏬👥

A **full-stack Python Flask project** for real-time crowd and parking monitoring. This system features **Admin and User dashboards**, **YOLOv8 video-based tracking**, **Socket.IO real-time updates**, and a **Gemini AI chatbot** integration.

---

## 📂 Project Structure

```text
CROWD_MONITORING_SYSTEM/
├── models/             # Pre-trained ML models (YOLOv8, Age, Gender)
├── static/             # CSS, JS, and UI images
├── templates/          # HTML templates (admin, user, login)
├── uploads/            # Temporary storage for uploaded videos
├── utils/              # Video processing & helper scripts
├── app.py              # Main Flask application entry point
├── README.md           # Project documentation
├── requirements.txt    # Python dependencies
└── yolov8n.pt          # YOLOv8 weights file

```

---

## ✨ Key Features

### 🛠️ Admin Dashboard

* **Parking Control:** Toggle slots (`A1`–`A6`) with instant global updates.
* **Crowd Management:** Upload entry videos to calculate total entries/exits.
* **Live Stats:** Monitor real-time occupancy data.

### 📱 User Dashboard

* **Live Availability:** Check crowd levels and parking spots before visiting.
* **AI Chatbot:** Text and Voice interaction via Web Speech API for mall FAQs.

### 🤖 Monitoring Logic

* **Detection:** Uses **YOLOv8** for high-accuracy person detection.
* **Tracking:** Centroid tracking for entry/exit flow.
* **Real-Time:** **Flask-SocketIO** ensures zero-refresh dashboard updates.

---

## ⚙️ System Requirements

* **Python:** 3.10+
* **Key Libs:** OpenCV, NumPy, Flask, Flask-SocketIO, Ultralytics (YOLOv8).
* **Hardware:** CPU (GPU recommended for faster processing).

---

## 🚀 Quick Setup & Run

### 1. Clone & Navigate

```bash
git clone <your-repo-url>
cd CROWD_MONITORING_SYSTEM

```

### 2. Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS / WSL
python3 -m venv venv
source venv/bin/activate

```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

```

### 4. Configure API Keys

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_actual_api_key_here

```

### 5. Launch

```bash
python app.py

```

> Access at: **http://127.0.0.1:5000**

| Role | Username | Password |
| --- | --- | --- |
| **Admin** | `admin` | `adminpass` |
| **User** | `user` | `userpass` |

---

## 🛠️ Usage & Deployment

### Step 6: Using the Project

* **Admin:** Upload a `.mp4` video in the panel to trigger the tracking script.
* **User:** View live stats or ask the chatbot "Is there parking available?"

### Optional: Advanced Tracking

To enable Age/Gender detection, place `age_net.caffemodel` and `gender_net.caffemodel` in the `/models` folder and update `utils/video_processing.py`.

### Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: Crowd Monitoring System"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main

```
