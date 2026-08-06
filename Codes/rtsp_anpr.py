"""
RTSP / simulation ANPR + flood monitoring pipeline.

The simulation path changes only the source and optional integrations. Every
simulation frame still passes through YOLO, plate cropping, preprocessing,
PaddleOCR recognition, validation, and multi-frame confirmation.

Controls:
  Q / ESC     quit
  SPACE       pause/resume simulation
  N           advance one simulation frame while paused
  R           restart the simulation source
  UP / DOWN   change simulated flood depth by 5 cm
  0           reset simulated flood depth

CPU installation:
  python -m pip install paddleocr paddlepaddle

GPU inference requires a PaddlePaddle GPU build compatible with the installed
CUDA version. Consult PaddlePaddle's installation selector; do not infer the
package from PyTorch CUDA availability.
"""

import csv
import os
import queue
import re
import sys
import time
import threading
from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
RUN_MODE = "SIMULATION"  # "LIVE" or "SIMULATION"

SIMULATION_SOURCE = "simulation/input.mp4"  # video, image, folder, or GENERATED
SIMULATION_LOOP = True
SIMULATION_USE_SUPABASE = False
SIMULATION_USE_SENSOR = False
SIMULATION_FPS = 15
SIMULATED_DEPTH_CM = 0.0
SIMULATION_SAVE_REPORT = True
SIMULATION_REPORT_PATH = "simulation/simulation_results.csv"

RTSP_URL = "rtsp://admin:camera2cd@192.168.0.59:554/Streaming/Channels/102"
CAMERA_ID = "89a69e50-9f46-46e7-a8e5-3304f54a34a6"
MODEL_PATH = "models/best.pt"
 
SERIAL_PORT = "COM6" #TO-DO Find a way to auto detect the serial port for the sensor
SERIAL_BAUD = 9600
SENSOR_ENABLED = True

WARNING_THRESHOLD_CM = 25.0
DANGER_THRESHOLD_CM = 40.0

CONFIDENCE_THRESHOLD = 0.5
YOLO_IMGSZ = 1280
OCR_EVERY_N_FRAMES = 5
MIN_PLATE_LEN = 5  # kept for legacy metrics; Malaysian validation no longer relies on it
OCR_CONF_THRESHOLD = 0.35
OCR_UPSCALE = 3
# Which preprocessing variants to run OCR on. "original" is always included.
# Fewer variants = faster OCR per frame (less CPU work), at a small cost to
# recognition robustness. Options: "original", "gray", "clahe".
OCR_VARIANTS = ["original", "gray", "clahe"]
OCR_HISTORY_SIZE = 7
OCR_MIN_MATCHES = 3
OCR_CONFIRMATION_RATIO = 0.6
TRACK_STALE_FRAMES = 30
DEDUP_SECONDS = 2.0
FLOOD_PUSH_INTERVAL = 3.0
ALERT_INTERVAL_SECONDS = 30.0
OUTPUT_DIR = "ocr_output"

# PaddleOCR 3.x recognition model used for Malaysian plates.
OCR_MODEL_NAME = "en_PP-OCRv5_mobile_rec"
# Alternative model for benchmarking:
# OCR_MODEL_NAME = "PP-OCRv6_small_rec"

# When True, push_detection() sends the expanded confidence payload that
# requires new Supabase columns. When False, it keeps the legacy
# database-compatible payload (single "confidence" field) while logs, CSV
# reports, overlays, and internal code still distinguish detector vs OCR
# confidence. See the Supabase migration note in the docs.
SUPABASE_EXTENDED_DETECTION_FIELDS = False

# Crop padding applied around the YOLO box before OCR so edge characters are
# less likely to be clipped.
PLATE_PAD_X_RATIO = 0.05
PLATE_PAD_Y_RATIO = 0.10

# Crop-quality rejection thresholds (initial configurable values).
OCR_MIN_CROP_WIDTH = 60
OCR_MIN_CROP_HEIGHT = 18
OCR_MIN_SHARPNESS = 20.0
OCR_MIN_MEAN_BRIGHTNESS = 15.0
OCR_MAX_MEAN_BRIGHTNESS = 245.0

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".m4v"}


# -----------------------------------------------------------------------------
# Optional imports
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
    from paddleocr import PaddleOCR
    try:
        from paddleocr import TextRecognition
    except ImportError:
        TextRecognition = None
    HAS_PADDLEOCR = True
except ImportError:
    PaddleOCR = None
    TextRecognition = None
    HAS_PADDLEOCR = False

try:
    import paddle
    HAS_PADDLE = True
except ImportError:
    HAS_PADDLE = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent


def resolve_path(value):
    """Resolve a user path against cwd, Codes/, and the project root."""
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    candidates = (Path.cwd() / path, SCRIPT_DIR / path, PROJECT_DIR / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return (SCRIPT_DIR / path).resolve()


def load_env():
    """Load Supabase credentials without requiring python-dotenv."""
    env_vars = {}
    for path in (SCRIPT_DIR / ".env.local", PROJECT_DIR / ".env.local", Path(".env.local")):
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip().strip('"').strip("'")
            print(f"[Config] Loaded environment variables from {path}")
            break
        except Exception as exc:
            print(f"[Config] Could not read {path}: {exc}")
    return env_vars


ENV = load_env()
SUPABASE_URL = ENV.get("NEXT_PUBLIC_SUPABASE_URL", "")
SUPABASE_KEY = ENV.get("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")


# -----------------------------------------------------------------------------
# Flood sensor and Supabase
# -----------------------------------------------------------------------------
class FloodSensor:
    RAW_EMPTY = 0.0
    RAW_FULL = 4095.0

    def __init__(self, port=SERIAL_PORT, baud=SERIAL_BAUD, enabled=SENSOR_ENABLED):
        self.port = port
        self.baud = baud
        self.enabled = bool(enabled and HAS_SERIAL)
        self.ser = None
        self.lock = threading.Lock()
        self.latest_raw = 0.0
        self.latest_depth_cm = 0.0
        self._stop = False
        self._thread = None
        if enabled and not HAS_SERIAL:
            print("[Sensor] pyserial is unavailable; sensor disabled.")
        if self.enabled:
            try:
                self.ser = serial.Serial(port, baud, timeout=0.5)
                print(f"[Sensor] Opened serial {port} @ {baud}")
                self._thread = threading.Thread(target=self._read_loop, daemon=True)
                self._thread.start()
            except Exception as exc:
                print(f"[Sensor] Could not open {port}: {exc}")
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
        span = self.RAW_FULL - self.RAW_EMPTY
        if span <= 0:
            return 0.0
        fraction = max(0.0, min(1.0, (raw - self.RAW_EMPTY) / span))
        return round(fraction * DANGER_THRESHOLD_CM * 2.0, 1)

    def get_depth_cm(self):
        with self.lock:
            return self.latest_depth_cm

    def close(self):
        self._stop = True
        if self._thread:
            self._thread.join(timeout=1.0)
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass


def flood_status(depth_cm):
    if depth_cm >= DANGER_THRESHOLD_CM:
        return "DANGER"
    if depth_cm >= WARNING_THRESHOLD_CM:
        return "WARNING"
    return "SAFE"


class SupabaseClient:
    def __init__(self, url, key, enabled=True):
        self.url = url.rstrip("/")
        self.key = key
        self.enabled = bool(enabled and HAS_REQUESTS and self.url and self.key)
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        self.registered_vehicles = {}
        self.last_detection_by_plate = {}
        self.last_flood_time = 0.0
        self.last_alert_time = 0.0
        self.total_detections = 0
        self.total_readings = 0
        self.total_alerts = 0

    def fetch_registered_vehicles(self):
        if not self.enabled:
            return
        try:
            response = requests.get(
                f"{self.url}/rest/v1/registered_vehicles?select=*",
                headers=self.headers,
                timeout=5,
            )
            if response.status_code == 200:
                vehicles = response.json()
                registered_vehicles = {}
                for item in vehicles:
                    normalized_plate = normalize_plate(item.get("plate_number", ""))
                    if normalized_plate:
                        registered_vehicles[normalized_plate] = item
                self.registered_vehicles = registered_vehicles
                print(f"[Supabase] Loaded {len(vehicles)} registered vehicles.")
            else:
                print(f"[Supabase Error {response.status_code}] Vehicle fetch.")
        except Exception as exc:
            print(f"[Supabase] Could not fetch registered vehicles: {exc}")

    def registration_label(self, plate):
        if not self.enabled:
            return "LOCAL"
        return "REGISTERED" if plate in self.registered_vehicles else "UNREGISTERED"

    def push_flood_reading(self, depth_cm, force=False):
        if not self.enabled:
            return
        now = time.time()
        if not force and now - self.last_flood_time < FLOOD_PUSH_INTERVAL:
            return
        self.last_flood_time = now
        try:
            payload = {
                "depth_cm": float(depth_cm),
                "status": flood_status(depth_cm),
                "sensor_id": "SENSOR-ESP32-01",
            }
            response = requests.post(
                f"{self.url}/rest/v1/flood_readings",
                json=payload,
                headers={**self.headers, "Prefer": "return=minimal"},
                timeout=3,
            )
            if response.status_code in (200, 201):
                self.total_readings += 1
            else:
                print(f"[Supabase Error {response.status_code}] Flood insert.")
        except Exception as exc:
            print(f"[Supabase] Flood insert exception: {exc}")

    def push_flood_alerts(self, depth_cm, force=False):
        if not self.enabled or flood_status(depth_cm) == "SAFE":
            return
        now = time.time()
        if not force and now - self.last_alert_time < ALERT_INTERVAL_SECONDS:
            return
        self.last_alert_time = now
        if not self.registered_vehicles:
            print("[Supabase] No registered vehicles to alert.")
            return
        status = flood_status(depth_cm)
        for plate, vehicle in self.registered_vehicles.items():
            vehicle_id = vehicle.get("id")
            if not vehicle_id:
                continue
            payload = {
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
            try:
                response = requests.post(
                    f"{self.url}/rest/v1/flood_alerts",
                    json=payload,
                    headers={**self.headers, "Prefer": "return=minimal"},
                    timeout=3,
                )
                if response.status_code in (200, 201):
                    self.total_alerts += 1
                else:
                    print(f"[Supabase Error {response.status_code}] Alert for {plate}.")
            except Exception as exc:
                print(f"[Supabase] Flood alert exception for {plate}: {exc}")

    def push_detection(
        self,
        plate_number,
        detector_confidence,
        ocr_confidence,
        consensus_ratio,
        consensus_matches,
        consensus_samples,
        track_id=None,
    ):
        if not self.enabled:
            return False
        plate = normalize_plate(plate_number)
        dedup_key = (plate, track_id)
        now = time.time()
        if now - self.last_detection_by_plate.get(dedup_key, 0.0) < DEDUP_SECONDS:
            return False
        self.last_detection_by_plate[dedup_key] = now
        vehicle = self.registered_vehicles.get(plate)
        if SUPABASE_EXTENDED_DETECTION_FIELDS:
            # Expanded payload requires new Supabase columns:
            #   detector_confidence, ocr_confidence, consensus_ratio,
            #   consensus_matches, consensus_samples
            payload = {
                "plate_number": plate,
                "detector_confidence": float(detector_confidence),
                "ocr_confidence": float(ocr_confidence),
                "consensus_ratio": float(consensus_ratio),
                "consensus_matches": int(consensus_matches),
                "consensus_samples": int(consensus_samples),
                "camera_id": CAMERA_ID,
                "vehicle_id": vehicle.get("id") if vehicle else None,
                "is_registered": vehicle is not None,
            }
        else:
            # Legacy database-compatible payload. The single "confidence"
            # field keeps the existing schema working; it is NOT presented as
            # OCR confidence anywhere in logs/reports/overlays.
            payload = {
                "plate_number": plate,
                "confidence": float(detector_confidence),
                "camera_id": CAMERA_ID,
                "vehicle_id": vehicle.get("id") if vehicle else None,
                "is_registered": vehicle is not None,
            }
        try:
            response = requests.post(
                f"{self.url}/rest/v1/plate_detections",
                json=payload,
                headers={**self.headers, "Prefer": "return=representation"},
                timeout=3,
            )
            if response.status_code in (200, 201):
                self.total_detections += 1
                print(
                    f"[Supabase] Detection {plate} "
                    f"[{self.registration_label(plate)}] "
                    f"det={detector_confidence:.2f} ocr={ocr_confidence:.2f} "
                    f"vote={consensus_matches}/{consensus_samples}"
                )
                return True
            print(f"[Supabase Error {response.status_code}] Detection insert.")
        except Exception as exc:
            print(f"[Supabase] Detection insert exception: {exc}")
        return False


class SupabaseWorker:
    """Runs Supabase network calls on a background thread.

    The main frame loop enqueues work and never blocks on HTTP. This removes
    the "sudden stutter" caused by synchronous requests.post() calls (which
    have multi-second timeouts) happening in the middle of video processing.
    """

    def __init__(self, client, maxsize=64):
        self.client = client
        self.queue = queue.Queue(maxsize=maxsize)
        self._stop = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while not self._stop:
            try:
                task = self.queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                kind = task[0]
                if kind == "flood_reading":
                    self.client.push_flood_reading(task[1], force=task[2])
                elif kind == "flood_alerts":
                    self.client.push_flood_alerts(task[1], force=task[2])
                elif kind == "detection":
                    self.client.push_detection(*task[1:])
            except Exception as exc:
                print(f"[SupabaseWorker] Task error: {exc}")
            finally:
                self.queue.task_done()

    def push_flood_reading(self, depth_cm, force=False):
        try:
            self.queue.put_nowait(("flood_reading", depth_cm, force))
        except queue.Full:
            pass  # Drop rather than block the frame loop.

    def push_flood_alerts(self, depth_cm, force=False):
        try:
            self.queue.put_nowait(("flood_alerts", depth_cm, force))
        except queue.Full:
            pass

    def push_detection(self, *args):
        try:
            self.queue.put_nowait(("detection",) + tuple(args))
        except queue.Full:
            pass

    def stop(self):
        self._stop = True
        if self._thread:
            self._thread.join(timeout=2.0)


# -----------------------------------------------------------------------------
# Input sources
# -----------------------------------------------------------------------------
class InputSource:
    def __init__(self, live, value, loop=True, fallback_fps=SIMULATION_FPS):
        self.live = live
        self.value = value
        self.loop = loop
        self.fallback_fps = max(1.0, float(fallback_fps))
        self.kind = "live" if live else ""
        self.cap = None
        self.image = None
        self.image_paths = []
        self.index = 0
        self.frame_number = 0
        self.fps = self.fallback_fps
        self.display_name = value
        self._open()

    def _open(self):
        if self.live:
            self.display_name = self.value
            self._open_capture(self.value, live=True)
            return
        if str(self.value).strip().upper() == "GENERATED":
            self.kind = "generated"
            self.display_name = "generated test sequence"
            return
        path = resolve_path(self.value)
        self.display_name = str(path)
        if path.is_dir():
            self.kind = "folder"
            self.image_paths = sorted(
                item for item in path.iterdir()
                if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS
            )
            if not self.image_paths:
                raise ValueError(f"No supported images found in {path}")
        elif path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            self.kind = "image"
            self.image = cv2.imread(str(path))
            if self.image is None:
                raise ValueError(f"Could not load image {path}")
        elif path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            self.kind = "video"
            self._open_capture(str(path), live=False)
        else:
            raise ValueError(
                f"Unsupported or missing simulation source: {path}. "
                "Use a video, image, image folder, or GENERATED."
            )

    def _open_capture(self, value, live):
        self.cap = cv2.VideoCapture(value)
        if live:
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not self.cap.isOpened():
            label = "RTSP stream" if live else "video"
            raise ValueError(f"Could not open {label}: {value}")
        self.kind = "live" if live else "video"
        native_fps = float(self.cap.get(cv2.CAP_PROP_FPS) or 0.0)
        if not live and 1.0 <= native_fps <= 240.0:
            self.fps = native_fps

    def _generated_frame(self):
        frame = np.full((720, 1280, 3), (55, 60, 65), dtype=np.uint8)
        offset = (self.index * 7) % 700
        cv2.rectangle(frame, (180 + offset, 250), (680 + offset, 570), (30, 30, 35), -1)
        cv2.rectangle(frame, (330 + offset, 450), (535 + offset, 515), (235, 235, 235), -1)
        cv2.putText(frame, "WKV8363", (342 + offset, 497), cv2.FONT_HERSHEY_SIMPLEX,
                    1.15, (10, 10, 10), 3, cv2.LINE_AA)
        self.index += 1
        return frame

    def read(self):
        if self.kind == "image":
            frame = self.image.copy()
        elif self.kind == "folder":
            if self.index >= len(self.image_paths):
                if not self.loop:
                    return False, None
                self.index = 0
            frame = cv2.imread(str(self.image_paths[self.index]))
            self.index += 1
            if frame is None:
                print("[Simulation] Skipping an unreadable image.")
                return self.read()
        elif self.kind == "generated":
            frame = self._generated_frame()
        else:
            ok, frame = self.cap.read()
            if not ok and self.kind == "video" and self.loop:
                self.restart()
                ok, frame = self.cap.read()
            if not ok:
                return False, None
        self.frame_number += 1
        return True, frame

    def restart(self):
        self.frame_number = 0
        self.index = 0
        if self.cap and self.kind == "video":
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def reconnect(self):
        if not self.live:
            return False
        if self.cap:
            self.cap.release()
        try:
            self._open_capture(self.value, live=True)
            return True
        except ValueError as exc:
            print(f"[Camera] Reconnect failed: {exc}")
            return False

    def close(self):
        if self.cap:
            self.cap.release()

    def overlay_name(self):
        if self.kind == "folder" and self.image_paths:
            current_index = max(0, min(self.index - 1, len(self.image_paths) - 1))
            return self.image_paths[current_index].name
        if self.kind == "generated":
            return self.display_name
        return Path(self.display_name).name


# -----------------------------------------------------------------------------
# PaddleOCR recognition-only adapter and parsing
# -----------------------------------------------------------------------------
def paddle_device():
    """Use a GPU only when PaddlePaddle confirms CUDA support."""
    if not HAS_PADDLE:
        return "cpu"
    try:
        if paddle.device.is_compiled_with_cuda() and paddle.device.cuda.device_count() > 0:
            return "gpu:0"
    except Exception:
        pass
    return "cpu"


class PaddlePlateRecognizer:
    """One OCR engine, using true recognition-only APIs for PaddleOCR 2.x/3.x."""
    def __init__(self):
        device = paddle_device()
        self.api = ""
        if TextRecognition is not None:
            print(f"[AI] Initializing PaddleOCR 3.x TextRecognition on {device}...")
            self.engine = TextRecognition(
                model_name=OCR_MODEL_NAME,
                device=device,
            )
            self.api = "v3-recognition"
        else:
            print(f"[AI] Initializing PaddleOCR 2.x recognition-only engine on {device}...")
            kwargs = {
                "lang": "en",
                "use_angle_cls": False,
                "show_log": False,
                "use_gpu": device.startswith("gpu"),
            }
            self.engine = PaddleOCR(**kwargs)
            self.api = "v2-recognition"

    def predict(self, image):
        if self.api == "v3-recognition":
            return self.engine.predict(input=image, batch_size=1)
        return self.engine.ocr(image, det=False, cls=False)


def normalize_plate(text: str) -> str:
    """Normalize OCR/registered plate text to uppercase alphanumerics."""
    return re.sub(r"[^A-Z0-9]", "", str(text).upper())


# Conservative pattern for common Malaysian private-vehicle plates:
# 1-3 letters, 1-4 digits, optional single trailing letter.
# Accepts e.g. B1, FC1, WKV8363, QAA1234A, SAB1234A.
# Rejects unrelated OCR text such as TOYOTA, MAL, CAR12345, 111111111.
#
# JPJePlate/EV plates: registration text remains uppercase Latin letters and
# digits, so no separate OCR alphabet is used. Results that consist only of
# visual labels (e.g. "MAL") are rejected by the pattern above; we do not
# blindly delete "MAL" from every result. Reliable JPJePlate recognition
# depends mainly on training data containing JPJePlate examples, accurate YOLO
# boxes around the registration text, adequate plate resolution, and good
# exposure/crop quality. No QR-code parsing is required.
COMMON_MY_PLATE_RE = re.compile(r"^[A-Z]{1,3}[0-9]{1,4}[A-Z]?$")


def validate_malaysian_plate(text: str) -> str:
    """Return a normalized plate if it matches a common Malaysian format."""
    plate = normalize_plate(text)

    if not plate:
        return ""

    if COMMON_MY_PLATE_RE.fullmatch(plate):
        return plate

    return ""


def _result_mapping(value):
    if isinstance(value, dict):
        return value
    for name in ("json", "res"):
        try:
            candidate = getattr(value, name)
            candidate = candidate() if callable(candidate) else candidate
            if isinstance(candidate, dict):
                return candidate
        except Exception:
            pass
    return None


def _collect_ocr_candidates(value, candidates, order=0, depth=0):
    """Extract text/score pairs from common PaddleOCR 2.x and 3.x shapes."""
    if value is None or depth > 7:
        return order
    mapping = _result_mapping(value)
    if mapping is not None:
        if "res" in mapping and mapping["res"] is not mapping:
            order = _collect_ocr_candidates(mapping["res"], candidates, order, depth + 1)
        texts = mapping.get("rec_texts")
        scores = mapping.get("rec_scores")
        if texts is not None:
            score_values = list(scores) if scores is not None else []
            for index, text in enumerate(list(texts)):
                score = score_values[index] if index < len(score_values) else 0.0
                try:
                    candidates.append((str(text), float(score), order))
                    order += 1
                except (TypeError, ValueError):
                    pass
        singular_text = mapping.get("rec_text", mapping.get("text"))
        singular_score = mapping.get(
            "rec_score", mapping.get("score", mapping.get("confidence"))
        )
        if singular_text is not None and singular_score is not None:
            try:
                candidates.append((str(singular_text), float(singular_score), order))
                order += 1
            except (TypeError, ValueError):
                pass
        return order
    if isinstance(value, (list, tuple)):
        if (
            len(value) == 2
            and isinstance(value[0], str)
            and isinstance(value[1], (int, float, np.floating))
        ):
            candidates.append((value[0], float(value[1]), order))
            return order + 1
        if (
            len(value) >= 2
            and isinstance(value[1], (list, tuple))
            and len(value[1]) >= 2
            and isinstance(value[1][0], str)
        ):
            try:
                candidates.append((value[1][0], float(value[1][1]), order))
                return order + 1
            except (TypeError, ValueError):
                pass
        for item in value:
            order = _collect_ocr_candidates(item, candidates, order, depth + 1)
    return order


def select_best_candidate(candidates):
    """Select the highest-confidence valid Malaysian plate from candidates.

    Candidates are (text, confidence, order) tuples. Each candidate is
    normalized and validated independently; identical normalized plates are
    deduplicated (keeping the highest confidence). Candidates are never
    concatenated.
    """
    best = {}
    for text, confidence, _order in candidates:
        plate = validate_malaysian_plate(text)
        if not plate:
            continue
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            continue
        if plate not in best or confidence > best[plate]:
            best[plate] = confidence
    if not best:
        return "", 0.0
    plate, confidence = max(best.items(), key=lambda item: item[1])
    return plate, float(confidence)


def recognize_plate(ocr_engine, processed_plate):
    """Recognize a YOLO crop and return the best valid plate/confidence."""
    if processed_plate is None or processed_plate.size == 0:
        return "", 0.0
    try:
        image = processed_plate
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        raw_result = ocr_engine.predict(image)
        candidates = []
        _collect_ocr_candidates(raw_result, candidates)
        return select_best_candidate(candidates)
    except Exception as exc:
        print(f"[OCR] Recognition warning: {type(exc).__name__}: {exc}")
        return "", 0.0


def make_plate_variants(plate):
    """Build a small set of preprocessing variants for OCR.

    Returns a list of (name, bgr_image) tuples. The original colour crop is
    preserved; grayscale and CLAHE variants are upscaled. Every returned image
    is a valid BGR image. Returns an empty list for invalid crops.
    """
    if plate is None or plate.size == 0:
        return []
    if len(plate.shape) == 2:
        plate = cv2.cvtColor(plate, cv2.COLOR_GRAY2BGR)
    height, width = plate.shape[:2]
    variants = [("original", plate.copy())]

    gray = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
    if OCR_UPSCALE > 1:
        gray = cv2.resize(
            gray,
            (width * OCR_UPSCALE, height * OCR_UPSCALE),
            interpolation=cv2.INTER_CUBIC,
        )
    if "gray" in OCR_VARIANTS:
        variants.append(("gray", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))

    # CLAHE avoids the contrast blow-out of global histogram equalization and
    # preserves thin character strokes better than aggressive denoising.
    if "clahe" in OCR_VARIANTS:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        clahe_gray = clahe.apply(gray)
        variants.append(("clahe", cv2.cvtColor(clahe_gray, cv2.COLOR_GRAY2BGR)))
    return variants


def recognize_best_variant(ocr_engine, plate_crop):
    """Run OCR on each preprocessing variant and return the best valid result.

    Returns (plate_text, ocr_confidence, selected_variant). Returns an empty
    result safely when all variants fail.
    """
    variants = make_plate_variants(plate_crop)
    best_text = ""
    best_confidence = 0.0
    best_variant = ""
    for name, image in variants:
        text, confidence = recognize_plate(ocr_engine, image)
        if text and confidence > best_confidence:
            best_text = text
            best_confidence = confidence
            best_variant = name
    return best_text, best_confidence, best_variant


class OcrWorker:
    """Runs PaddleOCR on a background thread.

    PaddleOCR runs on CPU in this environment (the installed paddle build has
    no CUDA), so each recognition call can take hundreds of milliseconds.
    Running it on a worker thread keeps the display loop responsive instead of
    freezing on every OCR frame.
    """

    def __init__(self, ocr_engine, maxsize=8):
        self.engine = ocr_engine
        self.queue = queue.Queue(maxsize=maxsize)
        self.results = {}
        self._lock = threading.Lock()
        self._stop = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while not self._stop:
            try:
                job_id, crop = self.queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                text, confidence, variant = recognize_best_variant(self.engine, crop)
                with self._lock:
                    self.results[job_id] = (text, confidence, variant)
            except Exception as exc:
                print(f"[OcrWorker] Recognition error: {exc}")
            finally:
                self.queue.task_done()

    def submit(self, job_id, crop):
        """Enqueue a crop for OCR. Returns True if accepted, False if dropped."""
        try:
            self.queue.put_nowait((job_id, crop))
            return True
        except queue.Full:
            return False

    def poll(self, job_id):
        """Return the result for job_id if ready, else None."""
        with self._lock:
            return self.results.pop(job_id, None)

    def stop(self):
        self._stop = True
        if self._thread:
            self._thread.join(timeout=2.0)


def padded_crop(
    frame,
    bbox,
    pad_x_ratio: float = PLATE_PAD_X_RATIO,
    pad_y_ratio: float = PLATE_PAD_Y_RATIO,
):
    """Return (padded_crop, (x1, y1, x2, y2)) with padding clamped to frame.

    Accepts a bounding box in x1, y1, x2, y2 format. Handles invalid and
    zero-area boxes safely by returning (None, None).
    """
    if frame is None or frame.size == 0:
        return None, None
    try:
        x1, y1, x2, y2 = (int(v) for v in bbox)
    except (TypeError, ValueError):
        return None, None
    height, width = frame.shape[:2]
    if x2 <= x1 or y2 <= y1:
        return None, None
    box_w = x2 - x1
    box_h = y2 - y1
    pad_x = int(box_w * pad_x_ratio)
    pad_y = int(box_h * pad_y_ratio)
    px1 = max(0, x1 - pad_x)
    py1 = max(0, y1 - pad_y)
    px2 = min(width, x2 + pad_x)
    py2 = min(height, y2 + pad_y)
    if px2 <= px1 or py2 <= py1:
        return None, None
    crop = frame[py1:py2, px1:px2]
    if crop.size == 0:
        return None, None
    return crop, (px1, py1, px2, py2)


def evaluate_crop_quality(plate_crop):
    """Return a dict describing crop quality and whether OCR should run."""
    result = {
        "accepted": False,
        "reason": "",
        "width": 0,
        "height": 0,
        "brightness": 0.0,
        "sharpness": 0.0,
    }
    if plate_crop is None or plate_crop.size == 0:
        result["reason"] = "empty"
        return result
    height, width = plate_crop.shape[:2]
    result["width"] = width
    result["height"] = height
    if width < OCR_MIN_CROP_WIDTH or height < OCR_MIN_CROP_HEIGHT:
        result["reason"] = "too_small"
        return result
    gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
    brightness = float(gray.mean())
    result["brightness"] = brightness
    if brightness < OCR_MIN_MEAN_BRIGHTNESS:
        result["reason"] = "too_dark"
        return result
    if brightness > OCR_MAX_MEAN_BRIGHTNESS:
        result["reason"] = "too_bright"
        return result
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    result["sharpness"] = sharpness
    if sharpness < OCR_MIN_SHARPNESS:
        result["reason"] = "blurry"
        return result
    result["accepted"] = True
    return result


# -----------------------------------------------------------------------------
# Per-track OCR confirmation and simulation reporting
# -----------------------------------------------------------------------------
@dataclass
class TrackState:
    history: deque = field(default_factory=lambda: deque(maxlen=OCR_HISTORY_SIZE))
    provisional_text: str = ""
    provisional_confidence: float = 0.0
    provisional_matches: int = 0
    provisional_samples: int = 0
    provisional_ratio: float = 0.0
    provisional_variant: str = ""
    confirmed_text: str = ""
    confirmed_confidence: float = 0.0
    confirmed_matches: int = 0
    confirmed_samples: int = 0
    confirmed_ratio: float = 0.0
    confirmed_variant: str = ""
    last_seen_frame: int = 0
    last_ocr_frame: int = -OCR_EVERY_N_FRAMES
    last_reported_plate: str = ""
    last_reported_matches: int = 0
    # Async OCR bookkeeping: the job id of an in-flight OCR request and the
    # crop/quality captured at submit time (used when the result arrives).
    pending_ocr_job: int = -1
    pending_crop: object = None
    pending_quality: dict = field(default_factory=dict)

    def add_reading(self, text, confidence, variant=""):
        """Record one OCR observation and update consensus metadata.

        Uses exact-string voting. Returns True when the plate becomes (or
        changes to) a newly confirmed plate, False otherwise.
        """
        self.history.append((text, confidence, variant))
        counts = Counter(item[0] for item in self.history)
        # Deterministic tie-break: highest vote count, then highest average
        # confidence, then lexicographically largest text.
        winner, matches = max(
            counts.items(),
            key=lambda item: (
                item[1],
                sum(score for value, score, _ in self.history if value == item[0])
                / item[1],
                item[0],
            ),
        )
        winner_scores = [score for value, score, _ in self.history if value == winner]
        average = sum(winner_scores) / len(winner_scores)
        samples = len(self.history)
        ratio = matches / samples
        winner_variant = next(
            (variant for value, _score, variant in reversed(self.history) if value == winner),
            "",
        )

        # When the provisional winner changes, clear stale confirmation
        # metadata so old results are not attached to the new winner.
        if winner != self.provisional_text:
            self.confirmed_text = ""
            self.confirmed_confidence = 0.0
            self.confirmed_matches = 0
            self.confirmed_samples = 0
            self.confirmed_ratio = 0.0
            self.confirmed_variant = ""

        self.provisional_text = winner
        self.provisional_confidence = average
        self.provisional_matches = matches
        self.provisional_samples = samples
        self.provisional_ratio = ratio
        self.provisional_variant = winner_variant

        if (
            matches >= OCR_MIN_MATCHES
            and ratio >= OCR_CONFIRMATION_RATIO
            and average >= OCR_CONF_THRESHOLD
        ):
            changed = self.confirmed_text != winner
            self.confirmed_text = winner
            self.confirmed_confidence = average
            self.confirmed_matches = matches
            self.confirmed_samples = samples
            self.confirmed_ratio = ratio
            self.confirmed_variant = winner_variant
            return changed
        return False


@dataclass
class SimulationMetrics:
    frames_processed: int = 0
    yolo_detections: int = 0
    accepted_ocr: int = 0
    rejected_ocr: int = 0
    confirmed_plates: set = field(default_factory=set)
    ocr_confidences: list = field(default_factory=list)
    processing_fps: list = field(default_factory=list)
    report_rows: list = field(default_factory=list)
    rejection_reasons: Counter = field(default_factory=Counter)

    def summary(self):
        avg_ocr = sum(self.ocr_confidences) / len(self.ocr_confidences) if self.ocr_confidences else 0.0
        avg_fps = sum(self.processing_fps) / len(self.processing_fps) if self.processing_fps else 0.0
        reasons = ", ".join(
            f"{reason}={count}" for reason, count in self.rejection_reasons.most_common()
        )
        reason_text = f", rejections({reasons})" if reasons else ""
        return (
            "[Simulation Summary] "
            f"frames={self.frames_processed}, yolo_detections={self.yolo_detections}, "
            f"accepted_ocr={self.accepted_ocr}, rejected_ocr={self.rejected_ocr}, "
            f"unique_confirmed_plates={len(self.confirmed_plates)}, "
            f"average_ocr_confidence={avg_ocr:.3f}, average_processing_fps={avg_fps:.2f}"
            f"{reason_text}"
        )

    def save_report(self, path):
        output_path = resolve_path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        columns = [
            "timestamp", "frame_number", "plate_number", "yolo_confidence",
            "ocr_confidence", "flood_depth_cm", "flood_status", "source",
            "selected_variant", "consensus_matches", "consensus_samples",
            "consensus_ratio", "crop_width", "crop_height", "crop_brightness",
            "crop_sharpness",
        ]
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            writer.writerows(self.report_rows)
        print(f"[Simulation] CSV report saved to {output_path}")


def draw_text(frame, text, position, color=(0, 255, 0), scale=0.7, thickness=2):
    cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX,
                scale, color, thickness, cv2.LINE_AA)


def draw_status_overlay(frame, source, fps, depth_cm, paused):
    status = flood_status(depth_cm)
    status_color = {"SAFE": (0, 220, 0), "WARNING": (0, 200, 255), "DANGER": (0, 0, 255)}[status]
    if source.live:
        lines = ["MODE: LIVE", f"FPS: {fps:.1f}"]
    else:
        lines = [
            "MODE: SIMULATION",
            f"SOURCE: {source.overlay_name()}",
            f"STATUS: {'PAUSED' if paused else 'PLAYING'}",
            f"FRAME: {source.frame_number}",
            f"FPS: {fps:.1f}",
        ]
    lines.append(f"FLOOD: {depth_cm:.1f} cm ({status})")
    panel_height = 18 + len(lines) * 28
    overlay = frame.copy()
    cv2.rectangle(overlay, (8, 8), (620, panel_height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    for index, line in enumerate(lines):
        color = status_color if line.startswith("FLOOD:") else (235, 235, 235)
        draw_text(frame, line, (20, 36 + index * 28), color, 0.65, 2)


class FallbackBoxTracker:
    """Small IoU tracker used only when Ultralytics does not return IDs."""
    def __init__(self, iou_threshold=0.25):
        self.iou_threshold = iou_threshold
        self.next_id = 1
        self.tracks = {}

    @staticmethod
    def _iou(first, second):
        ax1, ay1, ax2, ay2 = first
        bx1, by1, bx2, by2 = second
        intersection = max(0, min(ax2, bx2) - max(ax1, bx1)) * max(
            0, min(ay2, by2) - max(ay1, by1)
        )
        first_area = max(0, ax2 - ax1) * max(0, ay2 - ay1)
        second_area = max(0, bx2 - bx1) * max(0, by2 - by1)
        union = first_area + second_area - intersection
        return intersection / union if union else 0.0

    def assign(self, bbox, frame_number, claimed_ids):
        candidates = [
            (self._iou(bbox, data["bbox"]), track_id)
            for track_id, data in self.tracks.items()
            if track_id not in claimed_ids
            and frame_number - data["last_seen"] <= TRACK_STALE_FRAMES
        ]
        best_iou, track_id = max(candidates, default=(0.0, None))
        if track_id is None or best_iou < self.iou_threshold:
            track_id = f"fallback-{self.next_id}"
            self.next_id += 1
        self.tracks[track_id] = {"bbox": bbox, "last_seen": frame_number}
        claimed_ids.add(track_id)
        stale = [
            key for key, data in self.tracks.items()
            if frame_number - data["last_seen"] > TRACK_STALE_FRAMES
        ]
        for key in stale:
            del self.tracks[key]
        return track_id

    def reset(self):
        self.tracks.clear()
        self.next_id = 1


def extract_track_id(box):
    try:
        if box.id is not None:
            return int(box.id[0])
    except (AttributeError, IndexError, TypeError, ValueError):
        pass
    return None


def validate_runtime():
    mode = RUN_MODE.strip().upper()
    if mode not in {"LIVE", "SIMULATION"}:
        print(f"Unsupported RUN_MODE {RUN_MODE!r}. Use 'LIVE' or 'SIMULATION'.")
        return None
    missing = False
    if not HAS_CV2:
        print("OpenCV is required. Install with: pip install opencv-python")
        missing = True
    if not HAS_YOLO:
        print("Ultralytics is required. Install with: pip install ultralytics")
        missing = True
    if not HAS_PADDLEOCR or not HAS_PADDLE:
        print("PaddleOCR is required. Install with:\npip install paddleocr paddlepaddle")
        missing = True
    if missing:
        return None
    return mode


def main():
    mode = validate_runtime()
    if mode is None:
        return 1
    live = mode == "LIVE"
    use_sensor = SENSOR_ENABLED if live else SIMULATION_USE_SENSOR
    use_supabase = True if live else SIMULATION_USE_SUPABASE
    if use_supabase and not (SUPABASE_URL and SUPABASE_KEY):
        print("[Supabase] Credentials are required when Supabase is enabled.")
        return 1

    model_path = resolve_path(MODEL_PATH)
    if not model_path.exists():
        print(f"[AI] YOLO weights not found at {model_path}.")
        return 1
    yolo_device = 0 if HAS_TORCH and torch.cuda.is_available() else "cpu"
    print(f"[AI] Loading YOLO model from {model_path} on {yolo_device}...")
    model = YOLO(str(model_path))
    model.to(yolo_device)

    # Exactly one OCR adapter/underlying recognition model is initialized.
    ocr_engine = PaddlePlateRecognizer()
    sensor = FloodSensor(enabled=use_sensor)
    client = SupabaseClient(SUPABASE_URL, SUPABASE_KEY, enabled=use_supabase)
    client.fetch_registered_vehicles()

    # Background workers keep network (Supabase) and CPU (PaddleOCR) work off
    # the frame loop so the video never stutters on slow operations.
    supabase_worker = SupabaseWorker(client)
    ocr_worker = OcrWorker(ocr_engine)

    source_value = RTSP_URL if live else SIMULATION_SOURCE
    try:
        source = InputSource(live, source_value, SIMULATION_LOOP, SIMULATION_FPS)
    except ValueError as exc:
        print(f"[Source] {exc}")
        sensor.close()
        return 1
    print(f"[Source] MODE={mode}; active source: {source.display_name}")
    if not live and not use_supabase:
        print("[Simulation] Supabase disabled; all events remain local.")
    if not live and not use_sensor:
        print(f"[Simulation] Sensor disabled; starting depth={SIMULATED_DEPTH_CM:.1f} cm.")

    output_dir = resolve_path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics = SimulationMetrics()
    track_states = {}
    fallback_tracker = FallbackBoxTracker()
    simulated_depth = max(0.0, min(100.0, float(SIMULATED_DEPTH_CM)))
    previous_flood_status = None
    paused = False
    step_once = False
    last_display_frame = None
    last_processing_fps = 0.0
    previous_source_frame = 0

    try:
        while True:
            if not live and paused and not step_once:
                key = cv2.waitKeyEx(30)
                if key in (ord("q"), ord("Q"), 27):
                    break
                if key == 32:
                    paused = False
                elif key in (ord("n"), ord("N")):
                    step_once = True
                elif key in (ord("r"), ord("R")):
                    source.restart()
                    track_states.clear()
                    fallback_tracker.reset()
                    print("[Simulation] Source restarted.")
                elif key in (2490368, 65362):
                    simulated_depth = min(100.0, simulated_depth + 5.0)
                elif key in (2621440, 65364):
                    simulated_depth = max(0.0, simulated_depth - 5.0)
                elif key == ord("0"):
                    simulated_depth = 0.0
                if last_display_frame is not None:
                    display = last_display_frame.copy()
                    draw_status_overlay(display, source, last_processing_fps, simulated_depth, True)
                    cv2.imshow("ANPR + Flood", display)
                continue

            frame_started = time.perf_counter()
            ok, frame = source.read()
            if not ok:
                if live:
                    print("[Camera] Frame read failed; reconnecting...")
                    time.sleep(1.0)
                    track_states.clear()
                    fallback_tracker.reset()
                    source.reconnect()
                    continue
                print("[Simulation] Reached the end of the source.")
                break
            step_once = False
            frame_number = source.frame_number
            if frame_number <= previous_source_frame:
                track_states.clear()
                fallback_tracker.reset()
            previous_source_frame = frame_number
            depth_cm = sensor.get_depth_cm() if use_sensor else simulated_depth
            current_flood_status = flood_status(depth_cm)
            if not live and current_flood_status != previous_flood_status:
                print(f"[Simulation] Flood status: {current_flood_status} at {depth_cm:.1f} cm")
                previous_flood_status = current_flood_status
            supabase_worker.push_flood_reading(depth_cm)
            supabase_worker.push_flood_alerts(depth_cm)
            try:
                results = model.track(
                    frame,
                    imgsz=YOLO_IMGSZ,
                    device=yolo_device,
                    persist=True,
                    tracker="bytetrack.yaml",
                    verbose=False,
                )
            except Exception as exc:
                print(f"[AI] Tracking warning ({exc}); using detection for this frame.")
                results = model(frame, imgsz=YOLO_IMGSZ, device=yolo_device, verbose=False)

            fallback_claimed_ids = set()
            for result in results:
                for box in result.boxes:
                    yolo_confidence = float(box.conf[0])
                    if yolo_confidence < CONFIDENCE_THRESHOLD:
                        continue
                    metrics.yolo_detections += 1
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    height, width = frame.shape[:2]
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(width, x2), min(height, y2)
                    plate_crop = frame[y1:y2, x1:x2]
                    if plate_crop.size == 0:
                        continue
                    track_id = extract_track_id(box)
                    if track_id is None:
                        track_id = fallback_tracker.assign(
                            (x1, y1, x2, y2), frame_number, fallback_claimed_ids
                        )
                    state = track_states.setdefault(track_id, TrackState())
                    state.last_seen_frame = frame_number

                    newly_confirmed = False
                    # Poll for a previously submitted async OCR result first.
                    if state.pending_ocr_job >= 0:
                        result = ocr_worker.poll(state.pending_ocr_job)
                        if result is not None:
                            state.pending_ocr_job = -1
                            plate_text, ocr_confidence, selected_variant = result
                            padded = state.pending_crop
                            quality = state.pending_quality
                            state.pending_crop = None
                            state.pending_quality = {}
                            accepted = (
                                bool(plate_text)
                                and ocr_confidence >= OCR_CONF_THRESHOLD
                            )
                            if accepted:
                                metrics.accepted_ocr += 1
                                metrics.ocr_confidences.append(ocr_confidence)
                                newly_confirmed = state.add_reading(
                                    plate_text, ocr_confidence, selected_variant
                                )
                                # Only log a provisional result when the winner
                                # changes or its vote count changes meaningfully.
                                if (
                                    not state.confirmed_text
                                    and (
                                        state.provisional_text != state.last_reported_plate
                                        or state.provisional_matches != state.last_reported_matches
                                    )
                                ):
                                    state.last_reported_plate = state.provisional_text
                                    state.last_reported_matches = state.provisional_matches
                                    print(
                                        f"[Simulation] Provisional OCR: {state.provisional_text} "
                                        f"vote={state.provisional_matches}/{state.provisional_samples}"
                                        if not live
                                        else f"[OCR] Provisional: {state.provisional_text} "
                                        f"vote={state.provisional_matches}/{state.provisional_samples}"
                                    )
                            else:
                                metrics.rejected_ocr += 1

                    # Submit a new OCR job when due and none is in flight.
                    if (
                        frame_number - state.last_ocr_frame >= OCR_EVERY_N_FRAMES
                        and state.pending_ocr_job < 0
                    ):
                        state.last_ocr_frame = frame_number
                        # Pad the YOLO crop before OCR so edge characters are
                        # less likely to be clipped.
                        padded, padded_coords = padded_crop(frame, (x1, y1, x2, y2))
                        if padded is None:
                            continue
                        quality = evaluate_crop_quality(padded)
                        if not quality["accepted"]:
                            metrics.rejected_ocr += 1
                            metrics.rejection_reasons[quality["reason"]] += 1
                            continue
                        job_id = frame_number * 1000 + track_id
                        if ocr_worker.submit(job_id, padded):
                            state.pending_ocr_job = job_id
                            state.pending_crop = padded
                            state.pending_quality = quality

                    display_text = state.confirmed_text or state.provisional_text
                    confirmed = bool(state.confirmed_text)
                    color = (0, 220, 0) if confirmed else (0, 200, 255)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    if display_text:
                        prefix = "" if confirmed else "? "
                        if confirmed:
                            label = (
                                f"{prefix}{display_text} "
                                f"[{client.registration_label(display_text)}] "
                                f"OCR:{state.confirmed_confidence:.2f} "
                                f"VOTE:{state.confirmed_matches}/{state.confirmed_samples}"
                            )
                        else:
                            label = (
                                f"{prefix}{display_text} "
                                f"[{client.registration_label(display_text)}] "
                                f"OCR:{state.provisional_confidence:.2f} "
                                f"VOTE:{state.provisional_matches}/{state.provisional_samples}"
                            )
                        draw_text(frame, label, (x1, max(24, y1 - 10)), color, 0.7, 2)

                    if newly_confirmed:
                        plate = state.confirmed_text
                        metrics.confirmed_plates.add(plate)
                        timestamp = datetime.now()
                        # Save the padded OCR crop (the same crop OCR ran on).
                        if padded is not None:
                            cv2.imwrite(
                                str(output_dir / f"plate_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.jpg"),
                                padded,
                            )
                        registration = client.registration_label(plate)
                        print(
                            f"[{'Simulation' if not live else 'OCR'}] Confirmed plate: {plate} "
                            f"[{registration}] det={yolo_confidence:.2f} "
                            f"ocr={state.confirmed_confidence:.2f} "
                            f"vote={state.confirmed_matches}/{state.confirmed_samples} "
                            f"ratio={state.confirmed_ratio:.2f} "
                            f"variant={state.confirmed_variant} track={track_id}"
                        )
                        supabase_worker.push_detection(
                            plate,
                            yolo_confidence,
                            state.confirmed_confidence,
                            state.confirmed_ratio,
                            state.confirmed_matches,
                            state.confirmed_samples,
                            track_id,
                        )
                        metrics.report_rows.append({
                            "timestamp": timestamp.isoformat(timespec="milliseconds"),
                            "frame_number": frame_number,
                            "plate_number": plate,
                            "yolo_confidence": f"{yolo_confidence:.4f}",
                            "ocr_confidence": f"{state.confirmed_confidence:.4f}",
                            "flood_depth_cm": f"{depth_cm:.1f}",
                            "flood_status": current_flood_status,
                            "source": source.display_name,
                            "selected_variant": state.confirmed_variant,
                            "consensus_matches": state.confirmed_matches,
                            "consensus_samples": state.confirmed_samples,
                            "consensus_ratio": f"{state.confirmed_ratio:.4f}",
                            "crop_width": quality["width"],
                            "crop_height": quality["height"],
                            "crop_brightness": f"{quality['brightness']:.2f}",
                            "crop_sharpness": f"{quality['sharpness']:.2f}",
                        })

            stale_ids = [
                track_id for track_id, state in track_states.items()
                if frame_number - state.last_seen_frame > TRACK_STALE_FRAMES
            ]
            for track_id in stale_ids:
                del track_states[track_id]

            elapsed = max(time.perf_counter() - frame_started, 1e-9)
            last_processing_fps = 1.0 / elapsed
            metrics.frames_processed += 1
            metrics.processing_fps.append(last_processing_fps)
            draw_status_overlay(frame, source, last_processing_fps, depth_cm, paused)
            last_display_frame = frame.copy()
            cv2.imshow("ANPR + Flood", frame)

            delay_ms = 1 if live else max(1, int(1000.0 / source.fps - elapsed * 1000.0))
            key = cv2.waitKeyEx(delay_ms)
            if key in (ord("q"), ord("Q"), 27):
                break
            if not live:
                if key == 32:
                    paused = not paused
                elif key in (ord("r"), ord("R")):
                    source.restart()
                    track_states.clear()
                    fallback_tracker.reset()
                    print("[Simulation] Source restarted.")
                elif key in (2490368, 65362):
                    simulated_depth = min(100.0, simulated_depth + 5.0)
                elif key in (2621440, 65364):
                    simulated_depth = max(0.0, simulated_depth - 5.0)
                elif key == ord("0"):
                    simulated_depth = 0.0
    except KeyboardInterrupt:
        print("\n[Main] Interrupted.")
    finally:
        source.close()
        sensor.close()
        ocr_worker.stop()
        supabase_worker.stop()
        cv2.destroyAllWindows()
        if not live:
            print(metrics.summary())
            if SIMULATION_SAVE_REPORT:
                try:
                    metrics.save_report(SIMULATION_REPORT_PATH)
                except Exception as exc:
                    print(f"[Simulation] Could not save CSV report: {exc}")
        print(
            f"[Main] Done. Sent {client.total_detections} detections, "
            f"{client.total_readings} flood readings, {client.total_alerts} flood alerts."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
