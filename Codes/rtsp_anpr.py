"""
===============================================================================
RTSP ANPR + FLOOD MONITORING PIPELINE
===============================================================================
Connects to an RTSP camera, runs YOLO license-plate detection + EasyOCR,
reads a water-depth sensor from an ESP32 over Serial (see sensor.cpp),
and pushes everything to Supabase (plate_detections, flood_readings,
flood_alerts).

Controls (OpenCV window):
  - [Q] / [ESC] : Quit

Dependencies: see requirements.txt
===============================================================================
"""

import os
import sys
import time
import re
import threading
from datetime import datetime

# -----------------------------------------------------------------------------
# CONFIGURATION  (EDIT THESE)
# -----------------------------------------------------------------------------

# >>> PLACEHOLDER: put your RTSP camera URL here <<<
# Example: rtsp://admin:password@192.168.1.100:554/stream1
# Hikvision: 101 = main stream (high res), 102 = substream (low res)
RTSP_URL = "rtsp://admin:camera2cd@192.168.0.59:554/Streaming/Channels/102"

# Hardcoded camera UUID (only 1 camera in the system).
# Find it in Supabase -> cameras table, or leave as-is.
CAMERA_ID = "89a69e50-9f46-46e7-a8e5-3304f54a34a6"

# YOLO weights path (place best.pt at Codes/models/best.pt)
MODEL_PATH = "models/best.pt"

# ESP32 serial flood sensor (see sensor.cpp)
SERIAL_PORT = "COM6"          # Windows COM port for the ESP32
SERIAL_BAUD = 9600            # must match sensor.cpp (Serial.begin(9600))
SENSOR_ENABLED = True         # set False to disable serial reading

# Flood thresholds (cm) - used to compute SAFE / WARNING / DANGER
WARNING_THRESHOLD_CM = 25.0
DANGER_THRESHOLD_CM = 40.0

# Detection tuning
CONFIDENCE_THRESHOLD = 0.5    # min YOLO confidence
YOLO_IMGSZ = 1280             # YOLO inference size (higher = better for small plates)
OCR_EVERY_N_FRAMES = 5        # run OCR every N frames to save compute
MIN_PLATE_LEN = 5             # min cleaned plate length to accept
OCR_CONF_THRESHOLD = 0.35     # min EasyOCR confidence to accept a plate
OCR_UPSCALE = 3               # upscale factor before OCR (improves accuracy)
DEDUP_SECONDS = 2.0           # min gap between pushes of the same plate
FLOOD_PUSH_INTERVAL = 3.0     # seconds between flood_readings inserts
ALERT_INTERVAL_SECONDS = 30.0 # re-alert all vehicles every 30s while flooding

# Local output folder for cropped plates
OUTPUT_DIR = "ocr_output"

# -----------------------------------------------------------------------------
# Optional dependency imports with graceful fallbacks
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
    import serial
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

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

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


# -----------------------------------------------------------------------------
# Environment & configuration loader
# -----------------------------------------------------------------------------
def load_env():
    """Load Supabase credentials from .env.local if present."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(base_dir, ".env.local"),
        os.path.join(base_dir, "..", ".env.local"),
        ".env.local",
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


# -----------------------------------------------------------------------------
# ESP32 Serial Flood Sensor
# -----------------------------------------------------------------------------
class FloodSensor:
    """Reads raw ADC (0..4095) from the ESP32 over Serial and maps to cm."""

    # Calibration: raw ADC value at 0 cm and at full scale.
    # Adjust these to match your sensor placement (see sensor.cpp TH_LOW/TH_MIDDLE).
    RAW_EMPTY = 0.0      # raw reading when dry
    RAW_FULL = 4095.0    # raw reading when fully submerged

    def __init__(self, port=SERIAL_PORT, baud=SERIAL_BAUD, enabled=SENSOR_ENABLED):
        self.port = port
        self.baud = baud
        self.enabled = enabled and HAS_SERIAL
        self.ser = None
        self.lock = threading.Lock()
        self.latest_raw = 0.0
        self.latest_depth_cm = 0.0
        self._stop = False
        self._thread = None

        if self.enabled:
            try:
                self.ser = serial.Serial(port, baud, timeout=0.5)
                print(f"[Sensor] Opened serial {port} @ {baud}")
                self._thread = threading.Thread(target=self._read_loop, daemon=True)
                self._thread.start()
            except Exception as e:
                print(f"[Sensor] Could not open {port}: {e}")
                self.enabled = False

    def _read_loop(self):
        while not self._stop:
            try:
                line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                if line:
                    raw = float(line)
                    with self.lock:
                        self.latest_raw = raw
                        self.latest_depth_cm = self._raw_to_cm(raw)
            except Exception:
                time.sleep(0.1)

    def _raw_to_cm(self, raw):
        """Map raw ADC to depth in cm (linear)."""
        span = self.RAW_FULL - self.RAW_EMPTY
        if span <= 0:
            return 0.0
        frac = max(0.0, min(1.0, (raw - self.RAW_EMPTY) / span))
        return round(frac * DANGER_THRESHOLD_CM * 2.0, 1)  # scale to ~80cm full

    def get_depth_cm(self):
        with self.lock:
            return self.latest_depth_cm

    def get_raw(self):
        with self.lock:
            return self.latest_raw

    def close(self):
        self._stop = True
        if self._thread:
            self._thread.join(timeout=1.0)
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass


# -----------------------------------------------------------------------------
# Supabase client (thin REST wrapper)
# -----------------------------------------------------------------------------
class SupabaseClient:
    def __init__(self, url, key):
        self.url = url.rstrip("/")
        self.key = key
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        self.registered_vehicles = {}
        self.last_detection_time = 0
        self.last_flood_time = 0
        self.last_alert_time = 0
        self.total_detections = 0
        self.total_readings = 0
        self.total_alerts = 0

    def fetch_registered_vehicles(self):
        """Load registered vehicles into a dict keyed by plate_number."""
        if not (HAS_REQUESTS and self.url and self.key):
            return
        try:
            res = requests.get(
                f"{self.url}/rest/v1/registered_vehicles?select=*",
                headers=self.headers,
                timeout=5,
            )
            if res.status_code == 200:
                vehicles = res.json()
                self.registered_vehicles = {
                    v["plate_number"].upper(): v for v in vehicles
                }
                print(
                    f"[Supabase] Loaded {len(vehicles)} registered vehicles: "
                    f"{list(self.registered_vehicles.keys())}"
                )
        except Exception as e:
            print(f"[Supabase] Could not fetch registered vehicles: {e}")

    def get_flood_status(self, depth_cm):
        if depth_cm >= DANGER_THRESHOLD_CM:
            return "DANGER"
        elif depth_cm >= WARNING_THRESHOLD_CM:
            return "WARNING"
        return "SAFE"

    def push_flood_reading(self, depth_cm, force=False):
        """Insert a flood reading into Supabase (throttled)."""
        now = time.time()
        if not force and (now - self.last_flood_time < FLOOD_PUSH_INTERVAL):
            return
        self.last_flood_time = now
        status = self.get_flood_status(depth_cm)

        if not (HAS_REQUESTS and self.url and self.key):
            return

        try:
            payload = {
                "depth_cm": float(depth_cm),
                "status": status,
                "sensor_id": "SENSOR-ESP32-01",
            }
            res = requests.post(
                f"{self.url}/rest/v1/flood_readings",
                json=payload,
                headers={**self.headers, "Prefer": "return=minimal"},
                timeout=3,
            )
            if res.status_code in (200, 201):
                self.total_readings += 1
                print(f"[Supabase] Flood reading {depth_cm}cm ({status}) sent.")
            else:
                print(f"[Supabase Error {res.status_code}] Flood insert: {res.text}")
        except Exception as e:
            print(f"[Supabase] Flood insert exception: {e}")

    def push_flood_alerts(self, depth_cm, force=False):
        """Alert ALL registered vehicles when flood crosses WARNING/DANGER.

        Re-alerts every ALERT_INTERVAL_SECONDS while water stays above threshold.
        Creates one flood_alerts row per registered vehicle.
        """
        now = time.time()
        if not force and (now - self.last_alert_time < ALERT_INTERVAL_SECONDS):
            return
        self.last_alert_time = now

        status = self.get_flood_status(depth_cm)
        if status not in ("WARNING", "DANGER"):
            return

        if not (HAS_REQUESTS and self.url and self.key):
            return

        if not self.registered_vehicles:
            print("[Supabase] No registered vehicles to alert.")
            return

        try:
            for plate, vehicle in self.registered_vehicles.items():
                vehicle_id = vehicle.get("id")
                if not vehicle_id:
                    continue
                alert_payload = {
                    "vehicle_id": vehicle_id,
                    "plate_number": plate,
                    "flood_level_cm": float(depth_cm),
                    "alert_type": status,
                    "message": (
                        f"{status} Alert: Flood level reached {depth_cm:.1f}cm. "
                        f"Vehicle {plate} ({vehicle.get('owner_name', 'Unknown')}) "
                        f"in {vehicle.get('zone', 'Unknown')} may be at risk."
                    ),
                    "is_notified": True,
                    "is_acknowledged": False,
                }
                res = requests.post(
                    f"{self.url}/rest/v1/flood_alerts",
                    json=alert_payload,
                    headers={**self.headers, "Prefer": "return=minimal"},
                    timeout=3,
                )
                if res.status_code in (200, 201):
                    self.total_alerts += 1
                else:
                    print(
                        f"  [Alert Error {res.status_code}] "
                        f"for {plate}: {res.text}"
                    )
            print(
                f"[Supabase] Flood alert ({status}) sent to "
                f"{len(self.registered_vehicles)} registered vehicles "
                f"at {depth_cm:.1f}cm."
            )
        except Exception as e:
            print(f"[Supabase] Flood alert exception: {e}")

    def push_detection(self, plate_number, confidence, depth_cm):
        """Insert a plate detection; create a flood alert if registered + flooding."""
        now = time.time()
        if now - self.last_detection_time < DEDUP_SECONDS:
            return
        self.last_detection_time = now

        plate = plate_number.upper()
        vehicle = self.registered_vehicles.get(plate)
        is_registered = vehicle is not None
        vehicle_id = vehicle["id"] if vehicle else None

        if not (HAS_REQUESTS and self.url and self.key):
            return

        try:
            payload = {
                "plate_number": plate,
                "confidence": float(confidence),
                "camera_id": CAMERA_ID,
                "vehicle_id": vehicle_id,
                "is_registered": is_registered,
            }
            res = requests.post(
                f"{self.url}/rest/v1/plate_detections",
                json=payload,
                headers={**self.headers, "Prefer": "return=representation"},
                timeout=3,
            )
            if res.status_code in (200, 201):
                self.total_detections += 1
                print(
                    f"[Supabase] Detection {plate} "
                    f"[{'REGISTERED' if is_registered else 'UNREGISTERED'}] "
                    f"conf={confidence:.2f}"
                )
            else:
                print(f"[Supabase Error {res.status_code}] Detection insert: {res.text}")
        except Exception as e:
            print(f"[Supabase] Detection insert exception: {e}")


# -----------------------------------------------------------------------------
# OCR preprocessing helper
# -----------------------------------------------------------------------------
def preprocess_plate(plate):
    """Upscale and enhance a cropped plate for better OCR accuracy."""
    if plate is None or plate.size == 0:
        return plate
    # Upscale to improve OCR on small/low-res crops
    h, w = plate.shape[:2]
    if OCR_UPSCALE > 1:
        plate = cv2.resize(
            plate,
            (w * OCR_UPSCALE, h * OCR_UPSCALE),
            interpolation=cv2.INTER_CUBIC,
        )
    # Convert to grayscale and increase contrast
    gray = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    # Light denoise
    gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    return gray


# -----------------------------------------------------------------------------
# Main pipeline
# -----------------------------------------------------------------------------
def main():
    if not HAS_CV2:
        print("OpenCV (cv2) is required. Install: pip install opencv-python")
        sys.exit(1)

    # 1. Load YOLO model
    if not HAS_YOLO:
        print("ultralytics is required. Install: pip install ultralytics")
        sys.exit(1)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = MODEL_PATH
    if not os.path.exists(model_path):
        alt = os.path.join(base_dir, "..", "models", "best.pt")
        if os.path.exists(alt):
            model_path = alt
    if not os.path.exists(model_path):
        print(f"[AI] YOLO weights not found at {model_path}. Place best.pt there.")
        sys.exit(1)

    # Auto-detect compute device (GPU if available, else CPU)
    device = 0 if (HAS_TORCH and torch.cuda.is_available()) else "cpu"
    print(f"[AI] Using compute device: {device}")

    print(f"[AI] Loading YOLO model from {model_path}...")
    model = YOLO(model_path)
    model.to(device)

    # 2. Load EasyOCR (auto-detect GPU)
    if not HAS_EASYOCR:
        print("easyocr is required. Install: pip install easyocr")
        sys.exit(1)
    gpu = HAS_TORCH and torch.cuda.is_available()
    print(f"[AI] Initializing EasyOCR (gpu={gpu})...")
    reader = easyocr.Reader(["en"], gpu=gpu)

    # 3. Flood sensor
    sensor = FloodSensor()

    # 4. Supabase client
    client = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
    client.fetch_registered_vehicles()

    # 5. Open RTSP stream
    print(f"[Camera] Opening RTSP: {RTSP_URL}")
    cap = cv2.VideoCapture(RTSP_URL)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # reduce latency
    if not cap.isOpened():
        print("[Camera] Failed to open RTSP stream. Check URL/network.")
        sensor.close()
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    frame_count = 0
    last_plate = ""
    prev_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[Camera] Frame read failed - reconnecting...")
                cap.release()
                time.sleep(1.0)
                cap = cv2.VideoCapture(RTSP_URL)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                continue

            frame_count += 1

            # Current flood depth from ESP32
            depth_cm = sensor.get_depth_cm()

            # Periodically push flood reading
            client.push_flood_reading(depth_cm)

            # Alert all registered vehicles when flooding (re-alerts every 30s)
            client.push_flood_alerts(depth_cm)

            # YOLO detection (higher imgsz for small plates)
            results = model(frame, imgsz=YOLO_IMGSZ, device=device)
            for result in results:
                for box in result.boxes:
                    confidence = float(box.conf[0])
                    if confidence < CONFIDENCE_THRESHOLD:
                        continue

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    plate = frame[y1:y2, x1:x2]
                    if plate.size == 0:
                        continue

                    # OCR every N frames
                    plate_text = last_plate
                    if frame_count % OCR_EVERY_N_FRAMES == 0:
                        # Preprocess (upscale + enhance) for better OCR
                        processed = preprocess_plate(plate)
                        ocr = reader.readtext(processed)
                        if len(ocr) > 0:
                            new_text = ocr[0][1]
                            ocr_conf = float(ocr[0][2])
                            cleaned = re.sub(r"[^A-Z0-9]", "", new_text.upper())
                            # Only accept if confidence is high enough
                            if (
                                len(cleaned) >= MIN_PLATE_LEN
                                and ocr_conf >= OCR_CONF_THRESHOLD
                            ):
                                last_plate = cleaned
                                plate_text = cleaned

                    # Draw bounding box + plate text
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    if plate_text:
                        cv2.putText(
                            frame,
                            plate_text,
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 255, 0),
                            2,
                        )

                    # Save cropped plate locally
                    if plate_text:
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        cv2.imwrite(
                            os.path.join(OUTPUT_DIR, f"plate_{ts}.jpg"), plate
                        )

                    # Push detection to Supabase
                    if plate_text:
                        client.push_detection(plate_text, confidence, depth_cm)

            # FPS + depth overlay
            current_time = time.time()
            fps = 1 / (current_time - prev_time)
            prev_time = current_time

            cv2.putText(
                frame,
                f"FPS: {int(fps)}  Depth: {depth_cm:.1f}cm",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )

            cv2.imshow("RTSP ANPR + Flood", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
    except KeyboardInterrupt:
        print("\n[Main] Interrupted.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        sensor.close()
        print(
            f"[Main] Done. Sent {client.total_detections} detections, "
            f"{client.total_readings} flood readings, "
            f"{client.total_alerts} flood alerts."
        )


if __name__ == "__main__":
    main()
