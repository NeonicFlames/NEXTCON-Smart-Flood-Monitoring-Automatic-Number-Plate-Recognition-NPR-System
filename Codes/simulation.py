"""
===============================================================================
FLOOD MONITORING & AUTOMATIC NUMBER PLATE RECOGNITION (NPR) SYSTEM SIMULATOR
===============================================================================
This simulation integrates live computer vision (YOLO + EasyOCR or Synthetic Engine),
flood sensor depth modeling, and real-time telemetry output to Supabase / Local API.

Controls (OpenCV Window):
  - [W] / [UP]    : Increase water depth (+5 cm)
  - [S] / [DOWN]  : Decrease water depth (-5 cm)
  - [A]           : Toggle Auto-Tide Mode (simulated rising/falling flood water)
  - [V] / [SPACE] : Trigger simulated vehicle pass / plate detection
  - [C]           : Toggle Camera / YOLO mode vs Synthetic graphics mode
  - [Q] / [ESC]   : Quit simulation
===============================================================================
"""

import os
import sys
import time
import math
import random
import re
from datetime import datetime

# -----------------------------------------------------------------------------
# Optional Dependency Imports with Graceful Fallbacks
# -----------------------------------------------------------------------------
try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False


# -----------------------------------------------------------------------------
# Environment & Configuration Loader
# -----------------------------------------------------------------------------
def load_env():
    """Load Supabase credentials from .env.local if present."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(base_dir, ".env.local"),
        os.path.join(base_dir, "..", ".env.local"),
        ".env.local"
    ]
    env_vars = {}
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            env_vars[k.strip()] = v.strip().strip('"').strip("'")
                print(f"[Config] Loaded environment variables from {path}")
                break
            except Exception as e:
                print(f"[Config] Error reading {path}: {e}")
    return env_vars

ENV = load_env()
SUPABASE_URL = ENV.get("NEXT_PUBLIC_SUPABASE_URL", "")
SUPABASE_KEY = ENV.get("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
LOCAL_API_URL = "http://localhost:3000/api"

# Default camera UUID if available in database, or None
DEFAULT_CAMERA_UUID = "89a69e50-9f46-46e7-a8e5-3304f54a34a6"

# -----------------------------------------------------------------------------
# Fallback License Plates Pool (Including real registered vehicles in DB)
# -----------------------------------------------------------------------------
DEFAULT_PLATES = [
    {"plate": "ABC1234", "owner": "Ahmad Razak", "zone": "Zone A", "registered": True},
    {"plate": "XYZ8899", "owner": "Siti Aminah", "zone": "Zone A", "registered": True},
    {"plate": "WXX7777", "owner": "Tan Wei Liang", "zone": "Zone B", "registered": True},
    {"plate": "BND3384", "owner": "UNKNOWN", "zone": "Unregistered", "registered": False},
    {"plate": "PNG5521", "owner": "UNKNOWN", "zone": "Unregistered", "registered": False},
    {"plate": "SYR7011", "owner": "UNKNOWN", "zone": "Unregistered", "registered": False},
]


# -----------------------------------------------------------------------------
# Simulation State Manager
# -----------------------------------------------------------------------------
class SystemSimulation:
    def __init__(self):
        # Flood sensor state
        self.water_depth_cm = 12.0  # Base level 12 cm
        self.auto_tide = True
        self.tide_step = 0.0
        self.warning_threshold = 25.0
        self.danger_threshold = 40.0
        
        # Detection & Camera state
        self.use_yolo = False
        self.model = None
        self.reader = None
        self.cap = None
        self.video_source = None
        self.camera_id = DEFAULT_CAMERA_UUID
        
        # Registered vehicles map from Supabase
        self.registered_vehicles = {}
        self.sample_plates = list(DEFAULT_PLATES)
        
        # History & Telemetry logs
        self.detection_history = []
        self.last_flood_sync_time = 0
        self.last_detection_time = 0
        self.sync_status_msg = "Idle"
        self.total_synced_readings = 0
        self.total_synced_detections = 0
        
        # Animated Vehicle object in simulator canvas
        self.vehicle_x = -200
        self.current_vehicle = random.choice(self.sample_plates)
        
        self.fetch_registered_vehicles()
        self.init_ai_models()

    def fetch_registered_vehicles(self):
        """Fetch real registered vehicles from Supabase database."""
        if HAS_REQUESTS and SUPABASE_URL and SUPABASE_KEY:
            try:
                headers = {
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}"
                }
                res = requests.get(f"{SUPABASE_URL}/rest/v1/registered_vehicles?select=*", headers=headers, timeout=3)
                if res.status_code == 200:
                    vehicles = res.json()
                    if vehicles:
                        self.registered_vehicles = {v["plate_number"].upper(): v for v in vehicles}
                        print(f"[Supabase] Loaded {len(vehicles)} registered vehicles: {list(self.registered_vehicles.keys())}")
                        
                        # Build updated sample plates pool with real registered vehicles
                        new_samples = []
                        for v in vehicles:
                            new_samples.append({
                                "plate": v["plate_number"].upper(),
                                "owner": v["owner_name"],
                                "zone": v["zone"],
                                "registered": True
                            })
                        # Add unregistered plates
                        new_samples.extend([
                            {"plate": "BND3384", "owner": "UNKNOWN", "zone": "Unregistered", "registered": False},
                            {"plate": "PNG5521", "owner": "UNKNOWN", "zone": "Unregistered", "registered": False},
                            {"plate": "KCX9981", "owner": "UNKNOWN", "zone": "Unregistered", "registered": False},
                        ])
                        self.sample_plates = new_samples
                        self.current_vehicle = random.choice(self.sample_plates)
                        return
            except Exception as e:
                print(f"[Supabase] Could not fetch registered vehicles: {e}")

    def init_ai_models(self):
        """Attempt to initialize YOLO and EasyOCR if video and weights are present."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        weights_path = os.path.join(base_dir, "models", "best.pt")
        if not os.path.exists(weights_path):
            weights_path = os.path.join(base_dir, "..", "models", "best.pt")
            
        video_path = os.path.join(base_dir, "videos", "entrance.mp4")
        if not os.path.exists(video_path):
            video_path = os.path.join(base_dir, "..", "videos", "entrance.mp4")

        if HAS_YOLO and os.path.exists(weights_path):
            try:
                print(f"[AI] Loading YOLO model from {weights_path}...")
                self.model = YOLO(weights_path)
                self.use_yolo = True
            except Exception as e:
                print(f"[AI] YOLO load failed: {e}")

        if HAS_EASYOCR and self.use_yolo:
            try:
                print("[AI] Initializing EasyOCR Reader...")
                self.reader = easyocr.Reader(['en'], gpu=False)
            except Exception as e:
                print(f"[AI] EasyOCR load failed: {e}")

        if os.path.exists(video_path):
            try:
                self.cap = cv2.VideoCapture(video_path)
                self.video_source = video_path
                print(f"[Camera] Opened video source: {video_path}")
            except Exception as e:
                print(f"[Camera] Failed to open video: {e}")

    def update_flood_sensor(self):
        """Simulate dynamic water depth fluctuations (auto-tide sine wave)."""
        if self.auto_tide:
            self.tide_step += 0.05
            # Fluctuate water between 10cm and 52cm
            self.water_depth_cm = 30.0 + 22.0 * math.sin(self.tide_step)
            # Add small random ripple
            self.water_depth_cm += random.uniform(-0.4, 0.4)
            self.water_depth_cm = max(0.0, round(self.water_depth_cm, 1))

    def get_flood_status(self):
        if self.water_depth_cm >= self.danger_threshold:
            return "DANGER"
        elif self.water_depth_cm >= self.warning_threshold:
            return "WARNING"
        return "SAFE"

    def push_flood_reading_to_db(self, force=False):
        """Send current flood level to Supabase REST API or Local Next.js API."""
        now = time.time()
        # Push every 3 seconds unless forced
        if not force and (now - self.last_flood_sync_time < 3.0):
            return

        self.last_flood_sync_time = now
        status = self.get_flood_status()
        
        # 1. Try Supabase REST API directly
        if HAS_REQUESTS and SUPABASE_URL and SUPABASE_KEY:
            try:
                headers = {
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                }
                payload = {
                    "depth_cm": float(self.water_depth_cm),
                    "status": status,
                    "sensor_id": "SENSOR-SIM-01"
                }
                res = requests.post(
                    f"{SUPABASE_URL}/rest/v1/flood_readings",
                    json=payload,
                    headers=headers,
                    timeout=3
                )
                if res.status_code in (200, 201):
                    self.total_synced_readings += 1
                    self.sync_status_msg = f"Synced Supabase #{self.total_synced_readings}"
                    print(f"[Supabase Sync] Flood reading {self.water_depth_cm}cm ({status}) sent.")
                    return
                else:
                    print(f"[Supabase Error {res.status_code}] Flood reading insert failed: {res.text}")
            except Exception as e:
                self.sync_status_msg = f"Supabase sync err: {e}"

        # 2. Fallback to Local Next.js API route
        if HAS_REQUESTS:
            try:
                res = requests.post(
                    f"{LOCAL_API_URL}/flood-reading",
                    json={"depth_cm": float(self.water_depth_cm), "sensor_id": "SENSOR-SIM-01"},
                    timeout=2
                )
                if res.status_code == 200:
                    self.total_synced_readings += 1
                    self.sync_status_msg = f"Synced Local API #{self.total_synced_readings}"
                    print(f"[Local API Sync] Flood reading sent to Next.js server.")
                    return
            except Exception:
                pass
        
        self.sync_status_msg = "Standby (No active DB connection)"

    def push_detection_to_db(self, plate_data, confidence=0.95):
        """Send detected license plate event to Supabase or Local Next.js API."""
        now = time.time()
        if now - self.last_detection_time < 2.0:
            return  # Prevent duplicate rapid spam
        
        self.last_detection_time = now
        plate_num = plate_data["plate"].upper()

        # Check if plate is registered in database
        vehicle_info = self.registered_vehicles.get(plate_num)
        is_registered = vehicle_info is not None or plate_data.get("registered", False)
        vehicle_id = vehicle_info["id"] if vehicle_info else None
        owner = vehicle_info["owner_name"] if vehicle_info else plate_data.get("owner", "UNKNOWN")
        zone = vehicle_info["zone"] if vehicle_info else plate_data.get("zone", "Unregistered")

        # Log locally
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "plate": plate_num,
            "owner": owner,
            "registered": is_registered,
            "conf": confidence
        }
        self.detection_history.insert(0, entry)
        if len(self.detection_history) > 6:
            self.detection_history.pop()

        print(f"  --> Vehicle Detected: {plate_num} ({owner}) [{'REGISTERED' if is_registered else 'UNREGISTERED'}]")

        # 1. Direct Supabase insertion
        if HAS_REQUESTS and SUPABASE_URL and SUPABASE_KEY:
            try:
                headers = {
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation"
                }
                # Fix: camera_id must be a valid UUID or None!
                payload = {
                    "plate_number": plate_num,
                    "confidence": float(confidence),
                    "camera_id": self.camera_id,  # Valid UUID or None
                    "vehicle_id": vehicle_id,
                    "is_registered": is_registered
                }
                res = requests.post(
                    f"{SUPABASE_URL}/rest/v1/plate_detections",
                    json=payload,
                    headers=headers,
                    timeout=3
                )
                if res.status_code in (200, 201):
                    self.total_synced_detections += 1
                    print(f"[Supabase Sync] Plate detection {plate_num} inserted into 'plate_detections'.")

                    # If registered + flood warning/danger -> create flood_alert
                    flood_status = self.get_flood_status()
                    if is_registered and flood_status in ("WARNING", "DANGER") and vehicle_id:
                        alert_payload = {
                            "vehicle_id": vehicle_id,
                            "plate_number": plate_num,
                            "flood_level_cm": float(self.water_depth_cm),
                            "alert_type": flood_status,
                            "message": f"{flood_status} Alert: Vehicle {plate_num} ({owner}) detected in {zone} during flood depth {self.water_depth_cm:.1f}cm",
                            "is_notified": True,
                            "is_acknowledged": False
                        }
                        alert_res = requests.post(
                            f"{SUPABASE_URL}/rest/v1/flood_alerts",
                            json=alert_payload,
                            headers=headers,
                            timeout=3
                        )
                        if alert_res.status_code in (200, 201):
                            print(f"  [!] FLOOD ALERT generated in Supabase for {plate_num} ({flood_status})!")
                        else:
                            print(f"  [Alert Error {alert_res.status_code}] Could not create alert: {alert_res.text}")

                    return  # Success: exit early so we do not send a duplicate request via Local API

                else:
                    print(f"[Supabase Error {res.status_code}] Could not insert detection: {res.text}")
            except Exception as e:
                print(f"[Supabase Sync Exception] {e}")

        # 2. Local Next.js API detection route (fallback ONLY if direct Supabase failed or not configured)
        if HAS_REQUESTS:
            try:
                res = requests.post(
                    f"{LOCAL_API_URL}/detect",
                    json={
                        "plate_number": plate_num,
                        "confidence": float(confidence),
                        "camera_id": self.camera_id
                    },
                    timeout=2
                )
                if res.status_code == 200:
                    self.total_synced_detections += 1
                    print(f"[Local API] Sent detection {plate_num} to Next.js route.")
            except Exception:
                pass


# -----------------------------------------------------------------------------
# Graphical Renderer (OpenCV Canvas)
# -----------------------------------------------------------------------------
def render_gui(sim: SystemSimulation):
    """Draw a 1280x720 interactive dashboard using OpenCV."""
    canvas = np.zeros((720, 1280, 3), dtype=np.uint8)
    
    # Fill dark slate background
    canvas[:] = (20, 24, 32)
    
    # =========================================================================
    # LEFT PANEL: Camera Stream / Roadway Simulation (Width: 840, Height: 700)
    # =========================================================================
    left_x, left_y, left_w, left_h = 20, 20, 840, 680
    cv2.rectangle(canvas, (left_x, left_y), (left_x + left_w, left_y + left_h), (40, 45, 55), -1)
    cv2.rectangle(canvas, (left_x, left_y), (left_x + left_w, left_y + left_h), (70, 80, 100), 2)
    
    # Panel Title
    cv2.putText(canvas, "LIVE CAMERA / VEHICLE NPR FEED", (left_x + 20, left_y + 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220, 220, 240), 2)
    
    # Try video frame if camera mode enabled
    frame_rendered = False
    if sim.use_yolo and sim.cap and sim.cap.isOpened():
        ret, frame = sim.cap.read()
        if not ret:
            sim.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = sim.cap.read()
            
        if ret:
            frame_resized = cv2.resize(frame, (left_w - 40, left_h - 100))
            
            # Optional YOLO inference
            if sim.model:
                try:
                    results = sim.model(frame_resized, verbose=False)
                    for r in results:
                        for box in r.boxes:
                            if float(box.conf[0]) >= 0.5:
                                bx1, by1, bx2, by2 = map(int, box.xyxy[0])
                                cv2.rectangle(frame_resized, (bx1, by1), (bx2, by2), (0, 255, 120), 2)
                                cv2.putText(frame_resized, f"PLATE {float(box.conf[0]):.2f}", 
                                            (bx1, max(20, by1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 120), 2)
                except Exception:
                    pass

            canvas[left_y + 60: left_y + 60 + (left_h - 100), left_x + 20: left_x + 20 + (left_w - 40)] = frame_resized
            frame_rendered = True

    if not frame_rendered:
        # Render Synthetic Roadway & Vehicle Animation
        view_x1, view_y1 = left_x + 20, left_y + 60
        view_w, view_h = left_w - 40, left_h - 100
        
        # Roadway Sky / Ground
        cv2.rectangle(canvas, (view_x1, view_y1), (view_x1 + view_w, view_y1 + view_h), (35, 38, 48), -1)
        
        # Perspective Road
        pts_road = np.array([
            [view_x1 + 150, view_y1 + 100],
            [view_x1 + view_w - 150, view_y1 + 100],
            [view_x1 + view_w - 20, view_y1 + view_h],
            [view_x1 + 20, view_y1 + view_h]
        ], np.int32)
        cv2.fillPoly(canvas, [pts_road], (60, 65, 75))
        
        # Lane markings
        cv2.line(canvas, (view_x1 + view_w // 2, view_y1 + 100), (view_x1 + view_w // 2, view_y1 + view_h), (200, 200, 100), 2, cv2.LINE_AA)
        
        # Simulated Flood Water Overlay on road
        if sim.water_depth_cm > 5.0:
            water_height_px = int(min(view_h - 50, (sim.water_depth_cm / 60.0) * (view_h - 150)))
            water_y1 = view_y1 + view_h - water_height_px
            
            # Semi-transparent water overlay
            overlay = canvas.copy()
            cv2.rectangle(overlay, (view_x1 + 20, water_y1), (view_x1 + view_w - 20, view_y1 + view_h), (180, 110, 30), -1)
            
            # Water wave ripples
            for rx in range(view_x1 + 30, view_x1 + view_w - 30, 40):
                wy = water_y1 + int(4 * math.sin(rx * 0.05 + time.time() * 4))
                cv2.line(overlay, (rx, wy), (rx + 25, wy), (240, 180, 90), 2)
                
            alpha = 0.55
            cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0, canvas)

        # Animate passing vehicle
        sim.vehicle_x += 12
        if sim.vehicle_x > view_w + 100:
            sim.vehicle_x = -250
            sim.current_vehicle = random.choice(sim.sample_plates)

        car_cx = view_x1 + sim.vehicle_x
        car_cy = view_y1 + view_h - 180
        
        if view_x1 - 100 < car_cx < view_x1 + view_w + 100:
            # Draw vehicle body (SUV silhouette)
            cv2.rectangle(canvas, (car_cx - 110, car_cy - 40), (car_cx + 110, car_cy + 40), (100, 110, 130), -1)
            cv2.rectangle(canvas, (car_cx - 70, car_cy - 85), (car_cx + 60, car_cy - 40), (80, 90, 110), -1)
            # Wheels
            cv2.circle(canvas, (car_cx - 70, car_cy + 40), 22, (20, 20, 20), -1)
            cv2.circle(canvas, (car_cx + 70, car_cy + 40), 22, (20, 20, 20), -1)
            
            # Bounding Box for License Plate
            plate_x1, plate_y1 = car_cx - 45, car_cy + 5
            plate_x2, plate_y2 = car_cx + 45, car_cy + 30
            
            # Draw License Plate Box & Label
            cv2.rectangle(canvas, (plate_x1 - 5, plate_y1 - 5), (plate_x2 + 5, plate_y2 + 5), (0, 255, 0), 2)
            cv2.rectangle(canvas, (plate_x1, plate_y1), (plate_x2, plate_y2), (240, 240, 240), -1)
            cv2.putText(canvas, sim.current_vehicle["plate"], (plate_x1 + 4, plate_y1 + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (10, 10, 10), 2)

            # Auto trigger detection when car reaches center camera zone
            if view_x1 + view_w // 2 - 20 <= car_cx <= view_x1 + view_w // 2 + 20:
                sim.push_detection_to_db(sim.current_vehicle, confidence=0.96)
                
            # Detection Tag Label above vehicle
            cv2.rectangle(canvas, (car_cx - 80, car_cy - 120), (car_cx + 80, car_cy - 92), (0, 180, 80), -1)
            cv2.putText(canvas, f"NPR: {sim.current_vehicle['plate']}", (car_cx - 72, car_cy - 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    # =========================================================================
    # RIGHT PANEL: Telemetry, Flood Sensor & Database Controls (Width: 380)
    # =========================================================================
    right_x, right_y, right_w, right_h = 880, 20, 380, 680
    cv2.rectangle(canvas, (right_x, right_y), (right_x + right_w, right_y + right_h), (30, 34, 45), -1)
    cv2.rectangle(canvas, (right_x, right_y), (right_x + right_w, right_y + right_h), (70, 80, 100), 2)

    # Header
    cv2.putText(canvas, "SYSTEM TELEMETRY", (right_x + 20, right_y + 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 255), 2)

    # -------------------------------------------------------------------------
    # 1. Flood Water Gauge Bar
    # -------------------------------------------------------------------------
    gauge_x, gauge_y, gauge_w, gauge_h = right_x + 30, right_y + 70, 40, 200
    cv2.rectangle(canvas, (gauge_x, gauge_y), (gauge_x + gauge_w, gauge_y + gauge_h), (50, 55, 70), -1)
    cv2.rectangle(canvas, (gauge_x, gauge_y), (gauge_x + gauge_w, gauge_y + gauge_h), (120, 130, 150), 2)
    
    # Fill water height proportional to 60 cm max
    fill_h = int(min(gauge_h, (sim.water_depth_cm / 60.0) * gauge_h))
    status_str = sim.get_flood_status()
    
    if status_str == "DANGER":
        bar_color = (0, 0, 240)    # Bright Red
    elif status_str == "WARNING":
        bar_color = (0, 165, 255)  # Orange/Amber
    else:
        bar_color = (0, 210, 80)   # Green

    if fill_h > 0:
        cv2.rectangle(canvas, (gauge_x + 2, gauge_y + gauge_h - fill_h),
                      (gauge_x + gauge_w - 2, gauge_y + gauge_h - 2), bar_color, -1)

    # Threshold markers on gauge
    warn_y = gauge_y + gauge_h - int((sim.warning_threshold / 60.0) * gauge_h)
    danger_y = gauge_y + gauge_h - int((sim.danger_threshold / 60.0) * gauge_h)
    cv2.line(canvas, (gauge_x - 5, warn_y), (gauge_x + gauge_w + 5, warn_y), (0, 200, 255), 2)
    cv2.line(canvas, (gauge_x - 5, danger_y), (gauge_x + gauge_w + 5, danger_y), (0, 0, 255), 2)

    # Depth & Status text beside gauge
    info_x = gauge_x + gauge_w + 20
    cv2.putText(canvas, "FLOOD SENSOR #01", (info_x, gauge_y + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 190, 210), 1)
    cv2.putText(canvas, f"{sim.water_depth_cm:.1f} cm", (info_x, gauge_y + 55),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2)

    # Status Pill Box
    cv2.rectangle(canvas, (info_x, gauge_y + 75), (info_x + 160, gauge_y + 110), bar_color, -1)
    cv2.putText(canvas, f"STATUS: {status_str}", (info_x + 10, gauge_y + 98),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

    tide_mode_str = "AUTO TIDE (ON)" if sim.auto_tide else "MANUAL [W/S]"
    cv2.putText(canvas, f"Mode: {tide_mode_str}", (info_x, gauge_y + 135),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (160, 220, 180), 1)

    # -------------------------------------------------------------------------
    # 2. Database Sync Status Box
    # -------------------------------------------------------------------------
    db_box_y = right_y + 290
    cv2.rectangle(canvas, (right_x + 20, db_box_y), (right_x + right_w - 20, db_box_y + 70), (40, 46, 60), -1)
    cv2.rectangle(canvas, (right_x + 20, db_box_y), (right_x + right_w - 20, db_box_y + 70), (60, 70, 90), 1)
    
    cv2.putText(canvas, "CLOUD / DATABASE SYNC", (right_x + 30, db_box_y + 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1)
    cv2.putText(canvas, f"Readings: {sim.total_synced_readings} | Detections: {sim.total_synced_detections}",
                (right_x + 30, db_box_y + 42), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 210, 230), 1)
    cv2.putText(canvas, f"Status: {sim.sync_status_msg[:34]}", (right_x + 30, db_box_y + 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 250, 150), 1)

    # -------------------------------------------------------------------------
    # 3. Recent License Plate Detections Log
    # -------------------------------------------------------------------------
    log_y = db_box_y + 85
    cv2.putText(canvas, "RECENT DETECTED PLATES", (right_x + 20, log_y + 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 240), 1)
    
    log_box_y = log_y + 25
    cv2.rectangle(canvas, (right_x + 20, log_box_y), (right_x + right_w - 20, log_box_y + 150), (22, 26, 35), -1)
    
    line_offset = 20
    for idx, entry in enumerate(sim.detection_history[:5]):
        reg_icon = "[REG]" if entry["registered"] else "[UNK]"
        color = (100, 255, 100) if entry["registered"] else (100, 150, 255)
        text = f"{entry['time']}  {entry['plate']}  {reg_icon}"
        cv2.putText(canvas, text, (right_x + 30, log_box_y + line_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
        line_offset += 26

    # -------------------------------------------------------------------------
    # 4. Keyboard Controls Footer
    # -------------------------------------------------------------------------
    ctrl_y = right_h - 80
    cv2.putText(canvas, "KEYBOARD CONTROLS:", (right_x + 20, ctrl_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1)
    cv2.putText(canvas, "[W / S] Water Level +/-  | [A] Auto-Tide", (right_x + 20, ctrl_y + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 190, 200), 1)
    cv2.putText(canvas, "[V / Space] Trigger Vehicle Pass", (right_x + 20, ctrl_y + 38),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 190, 200), 1)
    cv2.putText(canvas, "[Q / ESC] Exit Simulation", (right_x + 20, ctrl_y + 56),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 190, 200), 1)

    return canvas


# -----------------------------------------------------------------------------
# Main Execution Loop
# -----------------------------------------------------------------------------
def run_simulation():
    print("\n=================================================================")
    print(" FLOOD MONITORING & NUMBER PLATE RECOGNITION (NPR) SIMULATOR ")
    print("=================================================================")
    print(f"Supabase Target : {SUPABASE_URL if SUPABASE_URL else 'Not configured (Local mode only)'}")
    print(f"OpenCV Window   : {'ENABLED' if HAS_CV2 else 'DISABLED (CLI Fallback)'}")
    print("=================================================================\n")

    sim = SystemSimulation()

    if HAS_CV2:
        window_name = "Smart Flood Monitoring & NPR Simulation System"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 1280, 720)

        while True:
            # Update sensor physics & database sync
            sim.update_flood_sensor()
            sim.push_flood_reading_to_db()

            # Render canvas frame
            frame = render_gui(sim)
            cv2.imshow(window_name, frame)

            # Process key events
            key = cv2.waitKey(30) & 0xFF
            if key in (ord('q'), ord('Q'), 27):  # ESC or Q
                print("[Simulator] Quitting...")
                break
            elif key in (ord('w'), ord('W'), 82):  # W or UP arrow
                sim.auto_tide = False
                sim.water_depth_cm = min(80.0, sim.water_depth_cm + 5.0)
                sim.push_flood_reading_to_db(force=True)
            elif key in (ord('s'), ord('S'), 84):  # S or DOWN arrow
                sim.auto_tide = False
                sim.water_depth_cm = max(0.0, sim.water_depth_cm - 5.0)
                sim.push_flood_reading_to_db(force=True)
            elif key in (ord('a'), ord('A')):
                sim.auto_tide = not sim.auto_tide
                print(f"[Simulator] Auto Tide mode: {sim.auto_tide}")
            elif key in (ord('v'), ord('V'), 32):  # V or Spacebar
                sim.vehicle_x = 350
                plate = random.choice(sim.sample_plates)
                sim.current_vehicle = plate
                sim.push_detection_to_db(plate)

        cv2.destroyAllWindows()
        if sim.cap:
            sim.cap.release()

    else:
        # Fallback CLI mode if OpenCV is not installed
        print("[CLI Mode] Running sensor telemetry background simulator...")
        try:
            while True:
                sim.update_flood_sensor()
                sim.push_flood_reading_to_db()
                status = sim.get_flood_status()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Water Depth: {sim.water_depth_cm:.1f} cm | Status: {status}")
                
                # Random vehicle pass every ~8 seconds
                if random.random() < 0.30:
                    plate = random.choice(sim.sample_plates)
                    sim.push_detection_to_db(plate)

                time.sleep(2)
        except KeyboardInterrupt:
            print("\n[Simulator] Stopped.")

if __name__ == "__main__":
    run_simulation()
