"""
RTSP ANPR + flood monitoring pipeline (rebuilt).

A single-file Windows application that reads one RTSP camera, detects licence
plates with YOLO, recognises Malaysian plates with EasyOCR, confirms plates
over multiple frames, reads a flood sensor over serial, and pushes readings,
alerts and confirmed detections to Supabase.

The highest-priority design goal is a SMOOTH, CURRENT, RESPONSIVE live video
window. The camera, display, YOLO, OCR, Supabase and serial sensor never block
one another. Stale camera frames are dropped rather than displayed late.

Controls:
  Q / ESC     quit

Threads:
  1. RTSP capture thread   - reads the stream, keeps only the newest frame
  2. YOLO detection thread - processes the newest pending frame
  3. OCR thread            - recognises plate crops
  4. Flood sensor thread   - reads serial, keeps the latest valid reading
  5. Supabase thread       - bounded background HTTP worker
  6. Main display loop     - OpenCV window + coordination
"""

import logging
import os
import queue
import re
import threading
import time
from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# -----------------------------------------------------------------------------
# 1. CONFIGURATION
# -----------------------------------------------------------------------------
RTSP_URL = "rtsp://admin:camera2cd@192.168.0.59:554/Streaming/Channels/101"
CAMERA_ID = "89a69e50-9f46-46e7-a8e5-3304f54a34a6"
MODEL_PATH = "models/best.pt"
OUTPUT_DIR = "ocr_output"

# Display window scale (0 < scale <= 1). The live frame is downscaled for the
# window so it fits on screen; detection/OCR still run on the full frame.
DISPLAY_SCALE = 0.5

# YOLO detection
YOLO_CONFIDENCE = 0.35
YOLO_IMAGE_SIZE = 640
MAX_DETECTION_FPS = 10          # ~10 detection operations per second

# OCR
OCR_CONFIDENCE_THRESHOLD = 0.40
# Confidence bonus applied when a single-character OCR confusion is corrected
# to a known registered plate. This nudges the corrected plate above the
# threshold and helps it win consensus over the misread.
OCR_CONFUSION_BONUS = 0.15
OCR_HISTORY_SIZE = 5
OCR_MIN_MATCHES = 3
OCR_CONFIRMATION_RATIO = 0.60
OCR_UPSCALE = 3
# EasyOCR recognition model. Default is "english_g2". Alternatives include
# "latin_g2" and other EasyOCR recognition networks. See EasyOCR docs.
OCR_RECOG_MODEL = "english_g2"
# Restrict OCR output to these characters. For licence plates, restricting to
# A-Z0-9 dramatically improves recognition by preventing punctuation/symbols
# from being output (which would otherwise fail Malaysian plate validation).
# Set to None to allow all characters.
OCR_ALLOWLIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
# Absolute minimum crop size (below this the crop is rejected as too small).
OCR_ABSOLUTE_MIN_CROP_WIDTH = 24
OCR_ABSOLUTE_MIN_CROP_HEIGHT = 8
# Preferred crop size. Crops below this are still accepted but marked for
# increased upscaling.
OCR_PREFERRED_CROP_WIDTH = 60
OCR_PREFERRED_CROP_HEIGHT = 18
# Sharpness thresholds. Small crops get a more lenient threshold because the
# Laplacian variance is unreliable on very small images.
OCR_MIN_SHARPNESS = 10.0
OCR_SMALL_CROP_MIN_SHARPNESS = 4.0
OCR_MIN_BRIGHTNESS = 15.0
OCR_MAX_BRIGHTNESS = 245.0

# Plate crop padding
PLATE_PAD_X_RATIO = 0.05
PLATE_PAD_Y_RATIO = 0.10

# Tracking
TRACK_STALE_SECONDS = 2.0
IOU_THRESHOLD = 0.25

# Flood sensor (serial)
SERIAL_PORT = "COM6"
SERIAL_BAUD = 9600
SENSOR_ENABLED = True
SENSOR_RAW_EMPTY = 0.0
SENSOR_RAW_FULL = 4095.0

# Flood thresholds
WARNING_THRESHOLD_CM = 25.0
DANGER_THRESHOLD_CM = 40.0

# Supabase
FLOOD_PUSH_INTERVAL = 3.0
ALERT_INTERVAL_SECONDS = 30.0
DETECTION_DEDUP_SECONDS = 2.0

# -----------------------------------------------------------------------------
# 2. IMPORTS AND DEPENDENCY CHECKS
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
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

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


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

log = logging.getLogger("anpr")


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
    """Load Supabase credentials from .env.local without python-dotenv."""
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
            log.info("Loaded environment variables from %s", path)
            break
        except Exception as exc:
            log.warning("Could not read %s: %s", path, exc)
    return env_vars


ENV = load_env()
SUPABASE_URL = ENV.get("NEXT_PUBLIC_SUPABASE_URL", "")
SUPABASE_KEY = ENV.get("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")


def validate_runtime():
    """Return True when all required components are present, else False."""
    missing = []
    if not HAS_CV2:
        missing.append("OpenCV (pip install opencv-python)")
    if not HAS_YOLO:
        missing.append("Ultralytics (pip install ultralytics)")
    if not HAS_EASYOCR:
        missing.append("EasyOCR (pip install easyocr)")
    if not HAS_TORCH:
        missing.append("PyTorch (see README for CUDA install)")
    if missing:
        log.error("Missing required components: %s", ", ".join(missing))
        return False
    return True


# -----------------------------------------------------------------------------
# 3. DATA CLASSES
# -----------------------------------------------------------------------------
@dataclass
class Detection:
    """A single YOLO plate detection."""
    bbox: tuple          # (x1, y1, x2, y2)
    confidence: float
    track_id: int = -1


@dataclass
class OcrResult:
    """A single OCR recognition result for a plate crop."""
    text: str
    confidence: float
    variant: str = ""


@dataclass
class TrackState:
    """Per-plate-track OCR consensus state."""
    history: deque = field(default_factory=lambda: deque(maxlen=OCR_HISTORY_SIZE))
    last_bbox: tuple = (0, 0, 0, 0)
    last_seen: float = 0.0
    best_crop: object = None
    best_sharpness: float = 0.0
    pending_ocr_job: int = -1
    last_ocr_time: float = 0.0
    reported: bool = False

    provisional_text: str = ""
    provisional_confidence: float = 0.0
    provisional_matches: int = 0
    provisional_samples: int = 0
    provisional_ratio: float = 0.0

    confirmed_text: str = ""
    confirmed_confidence: float = 0.0
    confirmed_matches: int = 0
    confirmed_samples: int = 0
    confirmed_ratio: float = 0.0

    # Raw OCR output (before Malaysian validation) for diagnostics. Lets the
    # dashboard show what EasyOCR actually read even when it does not yet
    # validate as a plate.
    raw_text: str = ""
    raw_confidence: float = 0.0

    # Last crop-quality rejection reason, for dashboard diagnostics.
    last_reject_reason: str = ""
    last_reject_dims: tuple = (0, 0)

    def add_reading(self, text, confidence):
        """Record one OCR observation and update consensus metadata.

        Returns True when the plate becomes (or changes to) a newly confirmed
        plate, False otherwise.
        """
        self.history.append((text, confidence))
        counts = Counter(item[0] for item in self.history)
        winner, matches = max(
            counts.items(),
            key=lambda item: (
                item[1],
                sum(score for value, score in self.history if value == item[0]) / item[1],
                item[0],
            ),
        )
        winner_scores = [score for value, score in self.history if value == winner]
        average = sum(winner_scores) / len(winner_scores)
        samples = len(self.history)
        ratio = matches / samples

        if winner != self.provisional_text:
            self.confirmed_text = ""
            self.confirmed_confidence = 0.0
            self.confirmed_matches = 0
            self.confirmed_samples = 0
            self.confirmed_ratio = 0.0

        self.provisional_text = winner
        self.provisional_confidence = average
        self.provisional_matches = matches
        self.provisional_samples = samples
        self.provisional_ratio = ratio

        if (
            matches >= OCR_MIN_MATCHES
            and ratio >= OCR_CONFIRMATION_RATIO
            and average >= OCR_CONFIDENCE_THRESHOLD
        ):
            changed = self.confirmed_text != winner
            self.confirmed_text = winner
            self.confirmed_confidence = average
            self.confirmed_matches = matches
            self.confirmed_samples = samples
            self.confirmed_ratio = ratio
            return changed
        return False


# -----------------------------------------------------------------------------
# 4. LATEST-FRAME BUFFER
# -----------------------------------------------------------------------------
class LatestItemBuffer:
    """Thread-safe buffer that keeps only the newest item.

    put() replaces any existing item (the old one is counted as dropped).
    get() returns and clears the newest item, or None when empty.
    This is the core anti-stutter primitive: a fast producer never builds a
    backlog, it simply overwrites the previous item.
    """

    def __init__(self):
        self._item = None
        self._cond = threading.Condition()
        self.dropped = 0

    def put(self, item):
        with self._cond:
            if self._item is not None:
                self.dropped += 1
            self._item = item
            self._cond.notify()

    def get(self, block=True, timeout=None):
        with self._cond:
            if block:
                self._cond.wait_for(lambda: self._item is not None, timeout)
            item = self._item
            self._item = None
            return item

    def peek(self):
        with self._cond:
            return self._item


# -----------------------------------------------------------------------------
# 5. CAMERA CAPTURE
# -----------------------------------------------------------------------------
class CameraCapture:
    """Dedicated RTSP capture thread that keeps only the newest frame."""

    def __init__(self, url, reconnect_delay=1.0):
        self.url = url
        self.reconnect_delay = reconnect_delay
        self.frames = LatestItemBuffer()
        self.connected = False
        self.capture_fps = 0.0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _open(self):
        cap = cv2.VideoCapture(self.url)
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        return cap

    def _run(self):
        cap = None
        frame_count = 0
        fps_window_start = time.perf_counter()
        while not self._stop.is_set():
            if cap is None or not cap.isOpened():
                self.connected = False
                log.warning("Camera disconnected; reconnecting...")
                if cap is not None:
                    cap.release()
                cap = self._open()
                if cap is None or not cap.isOpened():
                    if self._stop.wait(self.reconnect_delay):
                        break
                    continue
                self.connected = True
                log.info("Camera connected.")
                # Clear stale frames during reconnection.
                self.frames.get(block=False)
                self.frames.dropped = 0
                frame_count = 0
                fps_window_start = time.perf_counter()
                continue

            ok, frame = cap.read()
            if not ok:
                log.warning("Camera frame read failed.")
                cap.release()
                cap = None
                continue

            self.frames.put(frame)
            frame_count += 1
            now = time.perf_counter()
            if now - fps_window_start >= 1.0:
                self.capture_fps = frame_count / (now - fps_window_start)
                frame_count = 0
                fps_window_start = now

        if cap is not None:
            cap.release()
        log.info("Camera capture thread stopped.")

    def latest(self):
        """Return the newest frame, or None if none is available."""
        return self.frames.get(block=False)

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=3.0)


# -----------------------------------------------------------------------------
# 6. PLATE DETECTION (YOLO WORKER)
# -----------------------------------------------------------------------------
class YoloWorker:
    """Runs YOLO on a background thread over the newest pending frame."""

    def __init__(self, model, device, imgsz, max_fps):
        self.model = model
        self.device = device
        self.imgsz = imgsz
        self.min_interval = 1.0 / max(1.0, max_fps)
        self.pending = LatestItemBuffer()
        self._lock = threading.Lock()
        self.latest_result = []
        self.inference_time = 0.0
        self.detection_fps = 0.0
        self.total_detections = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def submit(self, frame):
        """Give the worker the newest frame (replaces any pending one)."""
        self.pending.put(frame)

    def latest(self):
        with self._lock:
            return list(self.latest_result)

    def _run(self):
        detections = 0
        window_start = time.perf_counter()
        while not self._stop.is_set():
            frame = self.pending.get(timeout=0.2)
            if frame is None:
                continue
            t0 = time.perf_counter()
            try:
                results = self.model(
                    frame,
                    imgsz=self.imgsz,
                    device=self.device,
                    verbose=False,
                )
            except Exception as exc:
                log.error("YOLO inference error: %s", exc)
                continue
            dt = time.perf_counter() - t0
            parsed = []
            for result in results:
                for box in result.boxes:
                    conf = float(box.conf[0])
                    if conf < YOLO_CONFIDENCE:
                        continue
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    parsed.append(Detection((x1, y1, x2, y2), conf))
            with self._lock:
                self.latest_result = parsed
                self.inference_time = dt
                self.total_detections += len(parsed)
            # Log when detections appear (throttled) so we can confirm YOLO
            # is actually finding plates.
            if parsed:
                log.info(
                    "YOLO detected %d plate(s) (conf>=%.2f): %s",
                    len(parsed), YOLO_CONFIDENCE,
                    [f"{d.confidence:.2f}" for d in parsed],
                )
            detections += 1
            now = time.perf_counter()
            if now - window_start >= 1.0:
                self.detection_fps = detections / (now - window_start)
                detections = 0
                window_start = now
            # Rate limit detection operations.
            elapsed = time.perf_counter() - t0
            if elapsed < self.min_interval:
                self._stop.wait(self.min_interval - elapsed)
        log.info("YOLO worker stopped.")

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=3.0)


# -----------------------------------------------------------------------------
# 7. OCR (EASYOCR WORKER)
# -----------------------------------------------------------------------------
def normalize_plate(text):
    """Normalize OCR/registered plate text to uppercase alphanumerics."""
    return re.sub(r"[^A-Z0-9]", "", str(text).upper())


# Conservative pattern for common Malaysian private-vehicle plates:
# 1-3 letters, 1-4 digits, optional single trailing letter.
# Accepts e.g. B1, FC1, WKV8363, QAA1234A, SAB1234A.
# Rejects unrelated OCR text such as TOYOTA, MAL, CAR12345, 111111111.
COMMON_MY_PLATE_RE = re.compile(r"^[A-Z]{1,3}[0-9]{1,4}[A-Z]?$")


def validate_malaysian_plate(text):
    """Return a normalized plate if it matches a common Malaysian format."""
    plate = normalize_plate(text)
    if not plate:
        return ""
    if COMMON_MY_PLATE_RE.fullmatch(plate):
        return plate
    return ""


# -----------------------------------------------------------------------------
# OCR character-confusion correction
# -----------------------------------------------------------------------------
# EasyOCR frequently confuses visually similar characters on licence plates.
# Each entry maps a misread character to the character(s) it is most likely to
# actually be. This is used to correct single-character OCR misreads (e.g. a
# "U" that should really be a "W") when the corrected plate matches a known
# registered vehicle. Corrections are only applied to the letter prefix of a
# plate, never to the digits, because digit misreads are far less common and
# correcting them risks false positives.
OCR_CONFUSIONS = {
    "U": "W",   # U <-> W (very common on Malaysian plates)
    "W": "U",
    "0": "O",   # zero <-> letter O
    "O": "0",
    "1": "I",   # one <-> letter I
    "I": "1",
    "8": "B",   # eight <-> letter B
    "B": "8",
    "5": "S",   # five <-> letter S
    "S": "5",
    "2": "Z",   # two <-> letter Z
    "Z": "2",
    "6": "G",   # six <-> letter G
    "G": "6",
    "4": "A",   # four <-> letter A
    "A": "4",
    "7": "T",   # seven <-> letter T
    "T": "7",
    "3": "E",   # three <-> letter E
    "E": "3",
    "9": "G",   # nine <-> letter G
    "G": "9",
}


def _confusion_variants(plate):
    """Yield single-character confusion variants of a normalized plate.

    For each character position, if that character has a known confusion
    mapping, yield the plate with that single character replaced by its
    confusion counterpart. Only one character is changed at a time so that
    genuine plates are never over-corrected.
    """
    for i, ch in enumerate(plate):
        replacement = OCR_CONFUSIONS.get(ch)
        if replacement:
            yield plate[:i] + replacement + plate[i + 1:]


def correct_plate_confusions(plate, registered):
    """Correct a single-character OCR misread against known registered plates.

    ``plate`` is a normalized, validated plate string. ``registered`` is an
    iterable of normalized registered plate strings (ground truth).

    If the plate itself is registered, it is returned unchanged. Otherwise, if
    exactly one single-character confusion variant matches a registered plate,
    that registered plate is returned (with a small confidence bonus). If zero
    or multiple variants match, the original plate is returned unchanged so we
    never guess.

    Returns (corrected_plate, corrected_confidence_bonus).
    """
    if not plate or not registered:
        return plate, 0.0
    if plate in registered:
        return plate, 0.0
    matches = [v for v in _confusion_variants(plate) if v in registered]
    if len(matches) == 1:
        return matches[0], OCR_CONFUSION_BONUS
    return plate, 0.0


def parse_easyocr_result(result):
    """Extract (text, confidence) candidates from an EasyOCR result.

    EasyOCR's readtext() returns a list of (bbox, text, confidence) tuples,
    so item[1] is the text string and item[2] is the confidence.
    """
    candidates = []
    if not result:
        return candidates
    for item in result:
        try:
            text = item[1]
            conf = item[2]
            candidates.append((str(text), float(conf)))
        except (TypeError, ValueError, IndexError):
            continue
    return candidates


def select_best_candidate(candidates, registered=None):
    """Select the highest-confidence valid Malaysian plate from candidates.

    Candidates are (text, confidence) tuples. Each is normalized and validated
    independently; identical normalized plates are deduplicated (keeping the
    highest confidence). Candidates are never concatenated.

    ``registered`` is an optional iterable of normalized registered plate
    strings. When provided, single-character OCR confusion misreads (e.g. a
    "U" that should be a "W") are corrected against the registered list, and
    the corrected plate receives a small confidence bonus so it can win over
    the misread.
    """
    registered = set(registered) if registered else set()
    best = {}
    for text, confidence in candidates:
        plate = validate_malaysian_plate(text)
        if not plate:
            continue
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            continue
        # Correct single-character OCR confusions against registered plates.
        corrected, bonus = correct_plate_confusions(plate, registered)
        if corrected != plate:
            plate = corrected
            confidence += bonus
        if plate not in best or confidence > best[plate]:
            best[plate] = confidence
    if not best:
        return "", 0.0
    plate, confidence = max(best.items(), key=lambda item: item[1])
    return plate, float(confidence)


def plate_upscale(width, height):
    """Return the upscale factor for a plate crop.

    Small crops (below the preferred size) get a larger adaptive upscale so
    readable but low-resolution plates are not lost. Capped to avoid
    excessive memory usage.
    """
    if width < OCR_PREFERRED_CROP_WIDTH or height < OCR_PREFERRED_CROP_HEIGHT:
        return min(max(OCR_UPSCALE, 4), 6)
    return OCR_UPSCALE


def preprocess_plate(crop, upscale=OCR_UPSCALE):
    """Single main preprocessing path: grayscale -> upscale -> CLAHE.

    Small crops (below the preferred size) are upscaled more aggressively so
    that readable but low-resolution plates are not lost. Only the cropped
    plate image is resized, never the full camera frame.
    """
    if crop is None or crop.size == 0:
        return None
    if len(crop.shape) == 2:
        gray = crop
    else:
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    # Use a larger adaptive upscale for small crops, capped to avoid
    # excessive memory usage.
    if w < OCR_PREFERRED_CROP_WIDTH or h < OCR_PREFERRED_CROP_HEIGHT:
        upscale = max(upscale, 4)
    upscale = min(upscale, 6)
    if upscale > 1:
        gray = cv2.resize(gray, (w * upscale, h * upscale), interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def _run_ocr(reader, image, registered=None):
    """Run EasyOCR on an image.

    Returns (valid_plate, valid_confidence, raw_text, raw_confidence).
    raw_text/raw_confidence are the highest-confidence raw OCR reading before
    Malaysian validation, used for diagnostics.

    ``registered`` is an optional iterable of normalized registered plate
    strings used to correct single-character OCR confusions.
    """
    if image is None or image.size == 0:
        return "", 0.0, "", 0.0
    try:
        kwargs = {}
        if OCR_ALLOWLIST:
            kwargs["allowlist"] = OCR_ALLOWLIST
        result = reader.readtext(image, **kwargs)
        candidates = parse_easyocr_result(result)
        plate, conf = select_best_candidate(candidates, registered)
        # Highest-confidence raw reading (any text) for diagnostics.
        raw_text, raw_conf = "", 0.0
        for text, c in candidates:
            if c > raw_conf:
                raw_text, raw_conf = text, c
        return plate, conf, raw_text, raw_conf
    except Exception as exc:
        log.warning("OCR recognition warning: %s: %s", type(exc).__name__, exc)
        return "", 0.0, "", 0.0


def recognize_plate(reader, crop, registered=None):
    """Recognize a plate crop with one main path and one fallback attempt.

    The fallback (original colour crop, no CLAHE) runs only when the primary
    path produces no text or confidence below the threshold.

    Returns (valid_plate, valid_confidence, raw_text, raw_confidence).
    """
    plate, conf, raw_text, raw_conf = _run_ocr(reader, preprocess_plate(crop), registered)
    if plate and conf >= OCR_CONFIDENCE_THRESHOLD:
        return plate, conf, raw_text, raw_conf
    plate2, conf2, raw2, raw2conf = _run_ocr(reader, crop, registered)
    if plate2 and conf2 > conf:
        return plate2, conf2, raw2, raw2conf
    # If the primary path read something but it didn't validate, prefer its raw
    # text for diagnostics; otherwise use the fallback's raw text.
    if raw_text:
        return plate, conf, raw_text, raw_conf
    return plate, conf, raw2, raw2conf


class OcrWorker:
    """Runs EasyOCR on a background thread over a bounded job queue."""

    def __init__(self, reader, maxsize=8):
        self.reader = reader
        self.queue = queue.Queue(maxsize=maxsize)
        self.results = {}
        self._lock = threading.Lock()
        self.inference_time = 0.0
        self._stop = threading.Event()
        self.registered = set()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def set_registered(self, registered):
        """Update the set of registered plates used for confusion correction."""
        with self._lock:
            self.registered = set(registered) if registered else set()

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

    def _run(self):
        while not self._stop.is_set():
            try:
                job_id, crop = self.queue.get(timeout=0.2)
            except queue.Empty:
                continue
            t0 = time.perf_counter()
            plate, conf, raw_text, raw_conf = recognize_plate(
                self.reader, crop, self.registered
            )
            dt = time.perf_counter() - t0
            with self._lock:
                self.results[job_id] = (plate, conf, raw_text, raw_conf)
                self.inference_time = dt
        log.info("OCR worker stopped.")

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=3.0)


# -----------------------------------------------------------------------------
# CROP QUALITY
# -----------------------------------------------------------------------------
def evaluate_crop_quality(plate_crop):
    """Return a dict describing crop quality and whether OCR should run.

    Crops below the absolute minimum are rejected as too small. Crops between
    the absolute minimum and the preferred size are accepted but marked with
    ``needs_upscale`` so the preprocessing step applies a larger upscale.
    Small crops also get a more lenient sharpness threshold.
    """
    result = {
        "accepted": False,
        "reason": "",
        "width": 0,
        "height": 0,
        "brightness": 0.0,
        "sharpness": 0.0,
        "needs_upscale": False,
    }
    if plate_crop is None or plate_crop.size == 0:
        result["reason"] = "empty"
        return result
    height, width = plate_crop.shape[:2]
    result["width"] = width
    result["height"] = height
    if (
        width < OCR_ABSOLUTE_MIN_CROP_WIDTH
        or height < OCR_ABSOLUTE_MIN_CROP_HEIGHT
    ):
        result["reason"] = "too_small"
        return result
    gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
    brightness = float(gray.mean())
    result["brightness"] = brightness
    if brightness < OCR_MIN_BRIGHTNESS:
        result["reason"] = "too_dark"
        return result
    if brightness > OCR_MAX_BRIGHTNESS:
        result["reason"] = "too_bright"
        return result
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    result["sharpness"] = sharpness
    # Small crops get a more lenient sharpness threshold because the
    # Laplacian variance is unreliable on very small images.
    is_small = (
        width < OCR_PREFERRED_CROP_WIDTH
        or height < OCR_PREFERRED_CROP_HEIGHT
    )
    min_sharpness = OCR_SMALL_CROP_MIN_SHARPNESS if is_small else OCR_MIN_SHARPNESS
    if sharpness < min_sharpness:
        result["reason"] = "blurry"
        return result
    result["needs_upscale"] = is_small
    result["accepted"] = True
    return result


def padded_crop(frame, bbox, pad_x_ratio=PLATE_PAD_X_RATIO, pad_y_ratio=PLATE_PAD_Y_RATIO):
    """Return (padded_crop, (x1, y1, x2, y2)) with padding clamped to frame."""
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


# -----------------------------------------------------------------------------
# 8. PLATE TRACKING AND CONSENSUS
# -----------------------------------------------------------------------------
def iou(first, second):
    """Intersection-over-union of two (x1, y1, x2, y2) boxes."""
    ax1, ay1, ax2, ay2 = first
    bx1, by1, bx2, by2 = second
    intersection = max(0, min(ax2, bx2) - max(ax1, bx1)) * max(
        0, min(ay2, by2) - max(ay1, by1)
    )
    first_area = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    second_area = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = first_area + second_area - intersection
    return intersection / union if union else 0.0


def associate_detections(detections, tracks, iou_threshold=IOU_THRESHOLD):
    """Associate detections to existing tracks by IoU.

    Returns a list of (track_id, detection) pairs. Detections that do not
    match an existing track get a fresh track id (negative, to be finalized by
    the caller).
    """
    assigned = []
    used = set()
    next_id = -1
    for det in detections:
        best_id = None
        best_iou = 0.0
        for tid, state in tracks.items():
            if tid in used:
                continue
            score = iou(det.bbox, state.last_bbox)
            if score > best_iou:
                best_iou = score
                best_id = tid
        if best_id is not None and best_iou >= iou_threshold:
            used.add(best_id)
            assigned.append((best_id, det))
        else:
            assigned.append((next_id, det))
            next_id -= 1
    return assigned


class PlateTracker:
    """Lightweight IoU-based plate tracker."""

    def __init__(self, iou_threshold=IOU_THRESHOLD, stale_seconds=TRACK_STALE_SECONDS):
        self.tracks = {}
        self.next_id = 1
        self.iou_threshold = iou_threshold
        self.stale_seconds = stale_seconds

    def update(self, detections, now):
        """Associate detections to tracks, updating boxes and timestamps."""
        pairs = associate_detections(detections, self.tracks, self.iou_threshold)
        for tid, det in pairs:
            if tid < 0:
                tid = self.next_id
                self.next_id += 1
                self.tracks[tid] = TrackState()
            state = self.tracks[tid]
            state.last_bbox = det.bbox
            state.last_seen = now
            det.track_id = tid

    def expire(self, now):
        stale = [
            tid for tid, state in self.tracks.items()
            if now - state.last_seen > self.stale_seconds
        ]
        for tid in stale:
            del self.tracks[tid]

    def clear(self):
        self.tracks.clear()


# -----------------------------------------------------------------------------
# 9. FLOOD SENSOR
# -----------------------------------------------------------------------------
def flood_status(depth_cm):
    if depth_cm >= DANGER_THRESHOLD_CM:
        return "DANGER"
    if depth_cm >= WARNING_THRESHOLD_CM:
        return "WARNING"
    return "SAFE"


class FloodSensor:
    """Serial flood sensor reader running on a background thread."""

    def __init__(self, port=SERIAL_PORT, baud=SERIAL_BAUD, enabled=SENSOR_ENABLED):
        self.port = port
        self.baud = baud
        self.enabled = bool(enabled and HAS_SERIAL)
        self.connected = False
        self._lock = threading.Lock()
        self.latest_depth_cm = 0.0
        self._stop = threading.Event()
        self._thread = None
        if enabled and not HAS_SERIAL:
            log.warning("pyserial is unavailable; sensor disabled.")
        if self.enabled:
            try:
                self.ser = serial.Serial(port, baud, timeout=0.5)
                self.connected = True
                log.info("Sensor connected on %s @ %s", port, baud)
                self._thread = threading.Thread(target=self._read_loop, daemon=True)
                self._thread.start()
            except Exception as exc:
                log.warning("Could not open %s: %s", port, exc)
                self.enabled = False

    def _read_loop(self):
        while not self._stop.is_set():
            try:
                line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                if line:
                    raw = float(line)
                    with self._lock:
                        self.latest_depth_cm = self._raw_to_cm(raw)
            except Exception:
                time.sleep(0.1)

    def _raw_to_cm(self, raw):
        span = SENSOR_RAW_FULL - SENSOR_RAW_EMPTY
        if span <= 0:
            return 0.0
        fraction = max(0.0, min(1.0, (raw - SENSOR_RAW_EMPTY) / span))
        return round(fraction * DANGER_THRESHOLD_CM * 2.0, 1)

    def get_depth_cm(self):
        with self._lock:
            return self.latest_depth_cm

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        if getattr(self, "ser", None):
            try:
                self.ser.close()
            except Exception:
                pass
        log.info("Sensor stopped.")


# -----------------------------------------------------------------------------
# 10. SUPABASE CLIENT AND WORKER
# -----------------------------------------------------------------------------
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
        if self.enabled:
            log.info("Supabase enabled.")
        else:
            log.warning("Supabase disabled (missing credentials or requests).")

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
                registered = {}
                for item in vehicles:
                    normalized = normalize_plate(item.get("plate_number", ""))
                    if normalized:
                        registered[normalized] = item
                self.registered_vehicles = registered
                log.info("Loaded %s registered vehicles.", len(vehicles))
            else:
                log.error("Supabase error %s fetching vehicles.", response.status_code)
        except Exception as exc:
            log.error("Could not fetch registered vehicles: %s", exc)

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
                log.error("Supabase error %s inserting flood reading.", response.status_code)
        except Exception as exc:
            log.error("Flood reading insert exception: %s", exc)

    def push_flood_alerts(self, depth_cm, force=False):
        if not self.enabled or flood_status(depth_cm) == "SAFE":
            return
        now = time.time()
        if not force and now - self.last_alert_time < ALERT_INTERVAL_SECONDS:
            return
        self.last_alert_time = now
        if not self.registered_vehicles:
            log.warning("No registered vehicles to alert.")
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
                    log.error("Supabase error %s inserting alert for %s.", response.status_code, plate)
            except Exception as exc:
                log.error("Flood alert insert exception for %s: %s", plate, exc)

    def push_detection(self, plate_number, detector_confidence, track_id=None):
        if not self.enabled:
            return False
        plate = normalize_plate(plate_number)
        dedup_key = (plate, track_id)
        now = time.time()
        if now - self.last_detection_by_plate.get(dedup_key, 0.0) < DETECTION_DEDUP_SECONDS:
            return False
        self.last_detection_by_plate[dedup_key] = now
        vehicle = self.registered_vehicles.get(plate)
        # Legacy database-compatible payload.
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
                log.info(
                    "Detection %s [%s] conf=%.2f",
                    plate, self.registration_label(plate), detector_confidence,
                )
                return True
            log.error("Supabase error %s inserting detection.", response.status_code)
        except Exception as exc:
            log.error("Detection insert exception: %s", exc)
        return False


class SupabaseWorker:
    """Runs Supabase network calls on a bounded background thread."""

    def __init__(self, client, maxsize=64):
        self.client = client
        self.queue = queue.Queue(maxsize=maxsize)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while not self._stop.is_set():
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
                log.error("Supabase worker task error: %s", exc)
            finally:
                self.queue.task_done()

    def push_flood_reading(self, depth_cm, force=False):
        try:
            self.queue.put_nowait(("flood_reading", depth_cm, force))
        except queue.Full:
            pass

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
        self._stop.set()
        self._thread.join(timeout=2.0)


# -----------------------------------------------------------------------------
# 11. DISPLAY HELPERS
# -----------------------------------------------------------------------------
def draw_text(frame, text, position, color=(0, 255, 0), scale=0.6, thickness=2):
    cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX,
                scale, color, thickness, cv2.LINE_AA)


def draw_status_overlay(frame, camera, yolo, ocr, depth_cm, display_fps, sensor_connected):
    status = flood_status(depth_cm)
    status_color = {"SAFE": (0, 220, 0), "WARNING": (0, 200, 255), "DANGER": (0, 0, 255)}[status]
    cam_state = "CONNECTED" if camera.connected else "RECONNECTING"
    sensor_state = "ON" if sensor_connected else "OFF"
    lines = [
        "MODE: LIVE",
        f"CAMERA: {cam_state}",
        f"CAPTURE FPS: {camera.capture_fps:.1f}",
        f"DISPLAY FPS: {display_fps:.1f}",
        f"DETECTION FPS: {yolo.detection_fps:.1f}",
        f"YOLO TIME: {yolo.inference_time * 1000:.0f} ms",
        f"YOLO DETECTIONS: {yolo.total_detections}",
        f"OCR TIME: {ocr.inference_time * 1000:.0f} ms",
        f"DROPPED FRAMES: {camera.frames.dropped}",
        f"SENSOR: {sensor_state}",
        f"FLOOD: {depth_cm:.1f} cm ({status})",
    ]
    panel_height = 18 + len(lines) * 24
    overlay = frame.copy()
    cv2.rectangle(overlay, (8, 8), (560, panel_height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    for index, line in enumerate(lines):
        color = status_color if line.startswith("FLOOD:") else (235, 235, 235)
        draw_text(frame, line, (20, 32 + index * 24), color, 0.55, 2)


def sanitize_filename(text):
    """Sanitize plate text for use in a filename."""
    return re.sub(r"[^A-Z0-9]", "", str(text).upper())


def draw_ocr_dashboard(frame, tracker, client):
    """Draw a simple OCR dashboard panel on the right side of the frame.

    Lists every active plate track with its current OCR status, plate text,
    confidence, vote count and registration label. Confirmed plates are shown
    in green, provisional ones in yellow.
    """
    h, w = frame.shape[:2]
    panel_w = 340
    x0 = w - panel_w - 8
    y0 = 8
    title = "OCR DASHBOARD"
    header_h = 34
    row_h = 26
    tracks = list(tracker.tracks.items())
    panel_h = header_h + len(tracks) * row_h + 16

    # Semi-transparent panel background.
    overlay = frame.copy()
    cv2.rectangle(overlay, (x0, y0), (x0 + panel_w, y0 + panel_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)
    cv2.rectangle(frame, (x0, y0), (x0 + panel_w, y0 + panel_h), (90, 90, 90), 1)

    draw_text(frame, title, (x0 + 12, y0 + 24), (0, 255, 255), 0.7, 2)

    if not tracks:
        draw_text(frame, "No plates detected", (x0 + 12, y0 + header_h + 20),
                  (200, 200, 200), 0.55, 2)
        return

    for index, (tid, state) in enumerate(tracks):
        y = y0 + header_h + index * row_h
        confirmed = bool(state.confirmed_text)
        text = state.confirmed_text or state.provisional_text
        if confirmed:
            color = (0, 220, 0)
            status = "CONFIRMED"
        elif text:
            color = (0, 200, 255)
            status = "PROVISIONAL"
        elif state.raw_text:
            color = (255, 160, 0)
            status = "OCR READING"
        elif state.pending_ocr_job >= 0:
            color = (0, 200, 255)
            status = "OCR QUEUED"
        elif state.last_reject_reason:
            color = (0, 0, 255)
            status = "CROP TOO SMALL" if state.last_reject_reason == "too_small" else "CROP REJECTED"
        else:
            color = (200, 200, 200)
            status = "PREPARING OCR"
        conf = state.confirmed_confidence if confirmed else state.provisional_confidence
        votes = state.confirmed_matches if confirmed else state.provisional_matches
        samples = state.confirmed_samples if confirmed else state.provisional_samples
        plate_display = text if text else (state.raw_text if state.raw_text else "---")
        reg = client.registration_label(plate_display) if text else ""
        line1 = f"#{tid}  {plate_display}  [{status}]"
        if text:
            line2 = f"    OCR:{conf:.2f}  VOTE:{votes}/{samples}  {reg}"
        elif state.raw_text:
            line2 = f"    RAW:{state.raw_text}  conf:{state.raw_confidence:.2f}"
        elif state.last_reject_reason:
            w, h = state.last_reject_dims
            line2 = f"    {state.last_reject_reason}: {w}x{h}"
        else:
            line2 = "    preparing crop for OCR..."
        draw_text(frame, line1, (x0 + 12, y + 16), color, 0.55, 2)
        draw_text(frame, line2, (x0 + 12, y + 16 + 16), (235, 235, 235), 0.45, 1)


# -----------------------------------------------------------------------------
# 12. MAIN APPLICATION
# -----------------------------------------------------------------------------
def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if not validate_runtime():
        return 1

    model_path = resolve_path(MODEL_PATH)
    if not model_path.exists():
        log.error("YOLO weights not found at %s", model_path)
        return 1

    # CUDA selection
    if HAS_TORCH and torch.cuda.is_available():
        yolo_device = 0
        log.info("CUDA selected (RTX 2060).")
    else:
        yolo_device = "cpu"
        log.warning("CUDA not available; falling back to CPU.")

    log.info("Loading YOLO model from %s on %s...", model_path, yolo_device)
    model = YOLO(str(model_path))
    model.to(yolo_device)
    # Warm up the model once during startup.
    warmup = np.zeros((YOLO_IMAGE_SIZE, YOLO_IMAGE_SIZE, 3), dtype=np.uint8)
    model(warmup, imgsz=YOLO_IMAGE_SIZE, device=yolo_device, verbose=False)
    log.info("YOLO model loaded and warmed up.")

    # EasyOCR shares the PyTorch CUDA environment.
    ocr_gpu = bool(HAS_TORCH and torch.cuda.is_available())
    log.info(
        "Initializing EasyOCR (gpu=%s, model=%s, allowlist=%s)...",
        ocr_gpu, OCR_RECOG_MODEL, "A-Z0-9" if OCR_ALLOWLIST else "all",
    )
    reader = easyocr.Reader(
        ["en"],
        gpu=ocr_gpu,
        recog_network=OCR_RECOG_MODEL,
    )
    log.info("EasyOCR initialized.")

    sensor = FloodSensor()
    client = SupabaseClient(SUPABASE_URL, SUPABASE_KEY, enabled=True)
    client.fetch_registered_vehicles()

    supabase_worker = SupabaseWorker(client)
    yolo_worker = YoloWorker(model, yolo_device, YOLO_IMAGE_SIZE, MAX_DETECTION_FPS)
    ocr_worker = OcrWorker(reader)
    # Feed the registered-vehicle list to the OCR worker so it can correct
    # single-character OCR confusions (e.g. U read as W) against ground truth.
    ocr_worker.set_registered(client.registered_vehicles.keys())

    camera = CameraCapture(RTSP_URL)
    log.info("Camera source configured (credentials hidden).")

    output_dir = resolve_path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    tracker = PlateTracker()
    job_counter = 0
    display_fps = 0.0
    display_frames = 0
    display_window_start = time.perf_counter()
    last_display_frame = None
    last_quality_log = 0.0
    last_submit_log = 0.0

    try:
        while True:
            frame = camera.latest()
            if frame is not None:
                # Give the newest frame to YOLO (replaces any pending one).
                yolo_worker.submit(frame)
                last_display_frame = frame

            # Latest available detection result (may be from an older frame).
            detections = yolo_worker.latest()
            now = time.time()
            tracker.update(detections, now)
            tracker.expire(now)

            # Submit OCR jobs for tracks that need them.
            for tid, state in tracker.tracks.items():
                if state.pending_ocr_job >= 0:
                    continue
                if now - state.last_ocr_time < 0.2:
                    continue
                if last_display_frame is None:
                    continue
                padded, _ = padded_crop(last_display_frame, state.last_bbox)
                if padded is None:
                    continue
                quality = evaluate_crop_quality(padded)
                if not quality["accepted"]:
                    state.last_reject_reason = quality["reason"]
                    state.last_reject_dims = (quality["width"], quality["height"])
                    # Log the rejection reason (throttled) so the user can see
                    # why OCR is not running.
                    if now - last_quality_log > 2.0:
                        last_quality_log = now
                        log.warning(
                            "Track %s crop rejected: %s (%dx%d)",
                            tid, quality["reason"], quality["width"],
                            quality["height"],
                        )
                    continue
                # Keep the sharpest crop for saving on confirmation.
                if quality["sharpness"] > state.best_sharpness:
                    state.best_crop = padded.copy()
                    state.best_sharpness = quality["sharpness"]
                upscale = plate_upscale(quality["width"], quality["height"])
                if now - last_submit_log > 2.0:
                    last_submit_log = now
                    log.info(
                        "Track %s crop accepted: %dx%d, upscale=%d",
                        tid, quality["width"], quality["height"], upscale,
                    )
                job_counter += 1
                job_id = job_counter
                if ocr_worker.submit(job_id, padded):
                    state.pending_ocr_job = job_id
                    state.last_ocr_time = now
                    if now - last_submit_log > 2.0:
                        last_submit_log = now
                        log.info("Track %s OCR job queued: %d", tid, job_id)

            # Poll OCR results and update consensus.
            for tid, state in tracker.tracks.items():
                if state.pending_ocr_job < 0:
                    continue
                result = ocr_worker.poll(state.pending_ocr_job)
                if result is None:
                    continue
                state.pending_ocr_job = -1
                text, conf, raw_text, raw_conf = result
                # Always record what EasyOCR actually read, for diagnostics.
                if raw_text:
                    state.raw_text = raw_text
                    state.raw_confidence = raw_conf
                if now - last_submit_log > 2.0:
                    last_submit_log = now
                    log.info(
                        "Track %s OCR completed: raw='%s', confidence=%.2f",
                        tid, raw_text, raw_conf,
                    )
                if not text or conf < OCR_CONFIDENCE_THRESHOLD:
                    if raw_text and not text:
                        log.info(
                            "OCR read '%s' (conf=%.2f) but it did not validate as a plate.",
                            raw_text, raw_conf,
                        )
                    continue
                newly_confirmed = state.add_reading(text, conf)
                if newly_confirmed:
                    plate = state.confirmed_text
                    log.info(
                        "Confirmed plate: %s [%s] ocr=%.2f vote=%d/%d ratio=%.2f track=%d",
                        plate, client.registration_label(plate),
                        state.confirmed_confidence, state.confirmed_matches,
                        state.confirmed_samples, state.confirmed_ratio, tid,
                    )
                    if not state.reported:
                        state.reported = True
                        # Save only the confirmed plate crop.
                        if state.best_crop is not None:
                            fname = (
                                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_"
                                f"{sanitize_filename(plate)}.jpg"
                            )
                            cv2.imwrite(str(output_dir / fname), state.best_crop)
                            log.info("Crop saved: %s", fname)
                        supabase_worker.push_detection(
                            plate, state.confirmed_confidence, tid,
                        )
                elif state.provisional_text:
                    log.info(
                        "Provisional OCR: %s vote=%d/%d",
                        state.provisional_text,
                        state.provisional_matches,
                        state.provisional_samples,
                    )

            # Draw on the newest frame.
            if last_display_frame is not None:
                display = last_display_frame.copy()
                # Downscale for the window. Boxes are in full-frame
                # coordinates, so scale them to match the display.
                scale = DISPLAY_SCALE
                if scale != 1.0:
                    display = cv2.resize(
                        display,
                        (int(display.shape[1] * scale), int(display.shape[0] * scale)),
                        interpolation=cv2.INTER_AREA,
                    )
                for tid, state in tracker.tracks.items():
                    x1, y1, x2, y2 = state.last_bbox
                    if scale != 1.0:
                        x1, y1, x2, y2 = (
                            int(x1 * scale), int(y1 * scale),
                            int(x2 * scale), int(y2 * scale),
                        )
                    confirmed = bool(state.confirmed_text)
                    color = (0, 220, 0) if confirmed else (0, 200, 255)
                    cv2.rectangle(display, (x1, y1), (x2, y2), color, 2)
                    text = state.confirmed_text or state.provisional_text
                    if text:
                        prefix = "" if confirmed else "? "
                        label = (
                            f"{prefix}{text} "
                            f"[{client.registration_label(text)}] "
                            f"OCR:{state.confirmed_confidence if confirmed else state.provisional_confidence:.2f}"
                        )
                        draw_text(display, label, (x1, max(24, y1 - 10)), color, 0.6, 2)
                draw_status_overlay(
                    display, camera, yolo_worker, ocr_worker,
                    sensor.get_depth_cm(), display_fps, sensor.connected,
                )
                draw_ocr_dashboard(display, tracker, client)
                cv2.imshow("ANPR + Flood", display)

            # Flood readings/alerts through the Supabase worker.
            depth_cm = sensor.get_depth_cm()
            supabase_worker.push_flood_reading(depth_cm)
            supabase_worker.push_flood_alerts(depth_cm)

            # Display FPS counter.
            display_frames += 1
            now_p = time.perf_counter()
            if now_p - display_window_start >= 1.0:
                display_fps = display_frames / (now_p - display_window_start)
                display_frames = 0
                display_window_start = now_p

            key = cv2.waitKeyEx(1)
            if key in (ord("q"), ord("Q"), 27):
                break
    except KeyboardInterrupt:
        log.info("Interrupted.")
    finally:
        log.info("Shutting down...")
        camera.stop()
        yolo_worker.stop()
        ocr_worker.stop()
        sensor.stop()
        supabase_worker.stop()
        cv2.destroyAllWindows()
        log.info(
            "Done. Sent %d detections, %d flood readings, %d flood alerts.",
            client.total_detections, client.total_readings, client.total_alerts,
        )
        log.info("Clean shutdown complete.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
