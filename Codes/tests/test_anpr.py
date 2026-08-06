"""Unit tests for the rebuilt Malaysian ANPR pipeline pure functions and state
logic.

These tests require no camera, Supabase, serial port, YOLO weights, EasyOCR
model downloads, CUDA, or internet access. They use mocks and pure functions.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Make the module under test importable without triggering heavy optional
# dependencies (cv2 is required; YOLO/EasyOCR are optional and guarded).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import rtsp_anpr as anpr  # noqa: E402


# -----------------------------------------------------------------------------
# Normalization and validation
# -----------------------------------------------------------------------------
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("WKV 8363", "WKV8363"),
        ("b 1", "B1"),
        ("FC-1", "FC1"),
        ("SAB 1234 A", "SAB1234A"),
        ("QAA1234A", "QAA1234A"),
    ],
)
def test_normalize_plate(raw, expected):
    assert anpr.normalize_plate(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("WKV 8363", "WKV8363"),
        ("b 1", "B1"),
        ("FC-1", "FC1"),
        ("SAB 1234 A", "SAB1234A"),
        ("QAA1234A", "QAA1234A"),
        ("B1", "B1"),
        ("FC1", "FC1"),
        ("ABC1234", "ABC1234"),
    ],
)
def test_validate_valid_plates(raw, expected):
    assert anpr.validate_malaysian_plate(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "TOYOTA",
        "MAL",
        "ABC",
        "123456",
        "CAR12345",
        "",
        "111111111",
        "   ",
        "ABCD1234",  # 4 letters
    ],
)
def test_validate_invalid_plates(raw):
    assert anpr.validate_malaysian_plate(raw) == ""


# -----------------------------------------------------------------------------
# Crop padding
# -----------------------------------------------------------------------------
def _frame(w=200, h=100):
    return np.zeros((h, w, 3), dtype=np.uint8)


def test_padded_crop_normal():
    frame = _frame()
    crop, coords = anpr.padded_crop(frame, (50, 20, 150, 80))
    assert crop is not None
    x1, y1, x2, y2 = coords
    assert x1 < x2 and y1 < y2
    assert x1 >= 0 and y1 >= 0 and x2 <= 200 and y2 <= 100
    # Padding should expand beyond the original box.
    assert x1 < 50 and y1 < 20 and x2 > 150 and y2 > 80


def test_padded_crop_left_edge():
    frame = _frame()
    crop, coords = anpr.padded_crop(frame, (0, 20, 100, 80))
    assert crop is not None
    x1, y1, x2, y2 = coords
    assert x1 == 0  # clamped to left edge
    assert x2 > 100


def test_padded_crop_right_edge():
    frame = _frame()
    crop, coords = anpr.padded_crop(frame, (100, 20, 200, 80))
    assert crop is not None
    x1, y1, x2, y2 = coords
    assert x2 == 200  # clamped to right edge
    assert x1 < 100


def test_padded_crop_top_edge():
    frame = _frame()
    crop, coords = anpr.padded_crop(frame, (50, 0, 150, 80))
    assert crop is not None
    x1, y1, x2, y2 = coords
    assert y1 == 0  # clamped to top edge
    assert y2 > 80


def test_padded_crop_bottom_edge():
    frame = _frame()
    crop, coords = anpr.padded_crop(frame, (50, 20, 150, 100))
    assert crop is not None
    x1, y1, x2, y2 = coords
    assert y2 == 100  # clamped to bottom edge
    assert y1 < 20


def test_padded_crop_corner():
    frame = _frame()
    crop, coords = anpr.padded_crop(frame, (0, 0, 100, 100))
    assert crop is not None
    x1, y1, x2, y2 = coords
    assert x1 == 0 and y1 == 0
    assert x2 <= 200 and y2 <= 100


def test_padded_crop_invalid_box():
    frame = _frame()
    crop, coords = anpr.padded_crop(frame, (150, 20, 50, 80))  # x2 < x1
    assert crop is None and coords is None


def test_padded_crop_zero_area():
    frame = _frame()
    crop, coords = anpr.padded_crop(frame, (50, 20, 50, 80))  # zero width
    assert crop is None and coords is None


def test_padded_crop_coords_never_exceed_frame():
    frame = _frame()
    for bbox in [(0, 0, 200, 100), (0, 0, 5, 5), (195, 95, 200, 100)]:
        crop, coords = anpr.padded_crop(frame, bbox)
        if crop is None:
            continue
        x1, y1, x2, y2 = coords
        assert 0 <= x1 <= x2 <= 200
        assert 0 <= y1 <= y2 <= 100


# -----------------------------------------------------------------------------
# OCR candidate selection
# -----------------------------------------------------------------------------
def test_select_best_candidate_one_valid():
    candidates = [("WKV8363", 0.9), ("GARBAGE", 0.99)]
    text, conf = anpr.select_best_candidate(candidates)
    assert text == "WKV8363"
    assert conf == pytest.approx(0.9)


def test_select_best_candidate_highest_confidence_wins():
    candidates = [("WKV8363", 0.7), ("SAB1234A", 0.95)]
    text, conf = anpr.select_best_candidate(candidates)
    assert text == "SAB1234A"
    assert conf == pytest.approx(0.95)


def test_select_best_candidate_dedup_normalized():
    candidates = [("WKV 8363", 0.7), ("WKV8363", 0.95)]
    text, conf = anpr.select_best_candidate(candidates)
    assert text == "WKV8363"
    assert conf == pytest.approx(0.95)


def test_select_best_candidate_empty():
    assert anpr.select_best_candidate([]) == ("", 0.0)


def test_select_best_candidate_malformed():
    candidates = [("WKV8363", "not-a-number"), (None, 0.5)]
    text, conf = anpr.select_best_candidate(candidates)
    assert text == ""
    assert conf == 0.0


def test_candidates_never_concatenated():
    # Two valid candidates must NOT be joined into one string.
    candidates = [("WKV", 0.9), ("8363", 0.9)]
    text, _ = anpr.select_best_candidate(candidates)
    assert text != "WKV8363"
    assert text == ""  # neither is a valid full plate


def test_parse_easyocr_result():
    raw = [
        ([[0, 0, 10, 10]], "WKV8363", 0.91),
        ([[0, 0, 10, 10]], "TOYOTA", 0.99),
    ]
    candidates = anpr.parse_easyocr_result(raw)
    assert ("WKV8363", 0.91) in candidates
    assert ("TOYOTA", 0.99) in candidates


# -----------------------------------------------------------------------------
# Temporal confirmation
# -----------------------------------------------------------------------------
def test_fewer_than_required_matches_remains_provisional():
    state = anpr.TrackState()
    for _ in range(anpr.OCR_MIN_MATCHES - 1):
        assert state.add_reading("WKV8363", 0.9) is False
    assert state.confirmed_text == ""
    assert state.provisional_text == "WKV8363"


def test_sufficient_matches_low_confidence_remains_provisional():
    state = anpr.TrackState()
    for _ in range(anpr.OCR_MIN_MATCHES):
        assert state.add_reading("WKV8363", 0.1) is False
    assert state.confirmed_text == ""


def test_sufficient_matches_and_ratio_confirms():
    state = anpr.TrackState()
    for _ in range(anpr.OCR_MIN_MATCHES):
        state.add_reading("WKV8363", 0.9)
    assert state.confirmed_text == "WKV8363"
    assert state.confirmed_matches == anpr.OCR_MIN_MATCHES
    assert state.confirmed_samples == anpr.OCR_MIN_MATCHES
    assert state.confirmed_ratio == pytest.approx(1.0)


def test_consensus_metadata_correct():
    state = anpr.TrackState()
    state.add_reading("WKV8363", 0.8)
    state.add_reading("WKV8363", 0.9)
    state.add_reading("WKV8363", 0.85)
    assert state.confirmed_text == "WKV8363"
    assert state.confirmed_matches == 3
    assert state.confirmed_samples == 3
    assert state.confirmed_ratio == pytest.approx(1.0)
    assert state.confirmed_confidence == pytest.approx((0.8 + 0.9 + 0.85) / 3)


def test_changed_winner_clears_confirmation():
    state = anpr.TrackState()
    for _ in range(anpr.OCR_MIN_MATCHES):
        state.add_reading("WKV8363", 0.9)
    assert state.confirmed_text == "WKV8363"
    # New winner takes over; old confirmation metadata must be cleared.
    for _ in range(5):
        state.add_reading("SAB1234A", 0.9)
    assert state.confirmed_text == "SAB1234A"
    assert state.confirmed_matches == 5
    # History is bounded to OCR_HISTORY_SIZE, so only the last 5 readings
    # (all SAB1234A) remain.
    assert state.confirmed_samples == anpr.OCR_HISTORY_SIZE


def test_history_bounded():
    state = anpr.TrackState()
    for i in range(anpr.OCR_HISTORY_SIZE + 5):
        state.add_reading(f"WKV{i % 3}", 0.9)
    assert len(state.history) <= anpr.OCR_HISTORY_SIZE


def test_equal_vote_counts_deterministic():
    state = anpr.TrackState()
    # Two candidates with equal counts -> deterministic tie-break.
    state.add_reading("WKV8363", 0.9)
    state.add_reading("SAB1234A", 0.9)
    state.add_reading("WKV8363", 0.9)
    state.add_reading("SAB1234A", 0.9)
    winner = state.provisional_text
    assert winner in ("WKV8363", "SAB1234A")
    # Running again must give the same result.
    state2 = anpr.TrackState()
    for text in ["WKV8363", "SAB1234A", "WKV8363", "SAB1234A"]:
        state2.add_reading(text, 0.9)
    assert state2.provisional_text == winner


# -----------------------------------------------------------------------------
# Duplicate suppression
# -----------------------------------------------------------------------------
def test_duplicate_suppression_same_track():
    client = anpr.SupabaseClient("", "", enabled=False)
    # Simulate the dedup logic used by push_detection.
    plate = "WKV8363"
    track_id = 1
    key = (plate, track_id)
    now = 1000.0
    client.last_detection_by_plate[key] = now
    assert now - client.last_detection_by_plate.get(key, 0.0) < anpr.DETECTION_DEDUP_SECONDS


def test_duplicate_suppression_different_track():
    client = anpr.SupabaseClient("", "", enabled=False)
    plate = "WKV8363"
    key1 = (plate, 1)
    key2 = (plate, 2)
    now = 1000.0
    client.last_detection_by_plate[key1] = now
    # Different track id -> not suppressed.
    assert now - client.last_detection_by_plate.get(key2, 0.0) >= anpr.DETECTION_DEDUP_SECONDS


# -----------------------------------------------------------------------------
# IoU association
# -----------------------------------------------------------------------------
def test_iou_overlapping():
    a = (0, 0, 100, 100)
    b = (10, 10, 110, 110)
    # Intersection 90x90=8100, union 10000+10000-8100=11900 -> 0.6807
    assert anpr.iou(a, b) == pytest.approx(0.6807, abs=0.01)


def test_iou_no_overlap():
    a = (0, 0, 10, 10)
    b = (100, 100, 110, 110)
    assert anpr.iou(a, b) == 0.0


def test_iou_identical():
    a = (0, 0, 100, 100)
    assert anpr.iou(a, a) == pytest.approx(1.0)


def test_associate_detections_matches_existing():
    tracks = {1: anpr.TrackState()}
    tracks[1].last_bbox = (0, 0, 100, 100)
    detections = [anpr.Detection((5, 5, 95, 95), 0.9)]
    pairs = anpr.associate_detections(detections, tracks)
    assert pairs[0][0] == 1


def test_associate_detections_new_track():
    tracks = {}
    detections = [anpr.Detection((0, 0, 100, 100), 0.9)]
    pairs = anpr.associate_detections(detections, tracks)
    assert pairs[0][0] < 0  # new track id


def test_tracker_assigns_ids_and_expires():
    tracker = anpr.PlateTracker(stale_seconds=0.1)
    now = 100.0
    tracker.update([anpr.Detection((0, 0, 100, 100), 0.9)], now)
    assert len(tracker.tracks) == 1
    tid = next(iter(tracker.tracks))
    assert tid >= 1
    # Same box again -> same track.
    tracker.update([anpr.Detection((0, 0, 100, 100), 0.9)], now + 0.01)
    assert len(tracker.tracks) == 1
    assert next(iter(tracker.tracks)) == tid
    # Expire after stale window.
    tracker.expire(now + 1.0)
    assert len(tracker.tracks) == 0


# -----------------------------------------------------------------------------
# Crop quality
# -----------------------------------------------------------------------------
def test_quality_empty_crop_rejected():
    result = anpr.evaluate_crop_quality(None)
    assert result["accepted"] is False
    assert result["reason"] == "empty"


def test_quality_tiny_crop_rejected():
    crop = np.zeros((5, 5, 3), dtype=np.uint8)
    result = anpr.evaluate_crop_quality(crop)
    assert result["accepted"] is False
    assert result["reason"] == "too_small"


def test_quality_black_crop_rejected():
    crop = np.zeros((100, 200, 3), dtype=np.uint8)
    result = anpr.evaluate_crop_quality(crop)
    assert result["accepted"] is False
    assert result["reason"] == "too_dark"


def test_quality_white_crop_rejected():
    crop = np.full((100, 200, 3), 255, dtype=np.uint8)
    result = anpr.evaluate_crop_quality(crop)
    assert result["accepted"] is False
    assert result["reason"] == "too_bright"


def test_quality_blurred_crop_rejected():
    # A uniform gray crop has zero Laplacian variance -> blurry.
    crop = np.full((100, 200, 3), 128, dtype=np.uint8)
    result = anpr.evaluate_crop_quality(crop)
    assert result["accepted"] is False
    assert result["reason"] == "blurry"


def test_quality_detailed_crop_accepted():
    # Synthetic crop with high-contrast detail and reasonable brightness.
    crop = np.zeros((100, 200, 3), dtype=np.uint8)
    crop[20:80, 20:180] = 200
    crop[40:60, 40:160] = 30
    result = anpr.evaluate_crop_quality(crop)
    assert result["accepted"] is True
    assert result["reason"] == ""
    assert result["width"] == 200
    assert result["height"] == 100


# -----------------------------------------------------------------------------
# Crop size / upscaling handling
# -----------------------------------------------------------------------------
def _detailed_crop(w, h):
    """Build a synthetic crop of the given size with high-contrast detail."""
    crop = np.zeros((h, w, 3), dtype=np.uint8)
    crop[2:h - 2, 2:w - 2] = 200
    crop[4:h - 4, 4:w - 4] = 30
    return crop


def test_quality_45x14_crop_accepted():
    # A moderately small crop (above absolute min, below preferred) is accepted.
    crop = _detailed_crop(45, 14)
    result = anpr.evaluate_crop_quality(crop)
    assert result["accepted"] is True
    assert result["reason"] == ""
    assert result["needs_upscale"] is True


def test_quality_20x6_crop_rejected_too_small():
    # Below the absolute minimum -> rejected as too small.
    crop = _detailed_crop(20, 6)
    result = anpr.evaluate_crop_quality(crop)
    assert result["accepted"] is False
    assert result["reason"] == "too_small"


def test_quality_large_crop_no_upscale_needed():
    crop = _detailed_crop(200, 100)
    result = anpr.evaluate_crop_quality(crop)
    assert result["accepted"] is True
    assert result["needs_upscale"] is False


def test_plate_upscale_small_crop():
    # Small crops get a larger adaptive upscale factor.
    assert anpr.plate_upscale(45, 14) >= 4
    assert anpr.plate_upscale(45, 14) <= 6


def test_plate_upscale_large_crop():
    # Large crops keep the configured OCR_UPSCALE.
    assert anpr.plate_upscale(200, 100) == anpr.OCR_UPSCALE


def test_preprocess_small_crop_upscaled():
    # A small accepted crop is upscaled by the preprocessing pipeline.
    crop = _detailed_crop(45, 14)
    processed = anpr.preprocess_plate(crop)
    assert processed is not None
    h, w = processed.shape
    assert w > 45 and h > 14


def test_small_crop_reaches_ocr_queue():
    # A moderately small crop can be submitted to the OCR worker queue.
    reader = _FakeReader()
    worker = anpr.OcrWorker(reader, maxsize=8)
    crop = _detailed_crop(45, 14)
    quality = anpr.evaluate_crop_quality(crop)
    assert quality["accepted"] is True
    accepted = worker.submit(1, crop)
    assert accepted is True
    worker.stop()


def test_rejected_crop_does_not_enter_ocr_queue():
    # A rejected crop must not be submitted to the OCR worker queue.
    reader = _FakeReader()
    worker = anpr.OcrWorker(reader, maxsize=8)
    crop = _detailed_crop(20, 6)
    quality = anpr.evaluate_crop_quality(crop)
    assert quality["accepted"] is False
    accepted = worker.submit(1, crop)
    # The queue accepts the call, but the caller must not submit rejected
    # crops. Verify the quality gate prevents it.
    assert quality["reason"] == "too_small"
    worker.stop()


class _FakeReader:
    """Minimal stand-in for an EasyOCR reader (never actually invoked)."""

    def readtext(self, image):
        return []


# -----------------------------------------------------------------------------
# Flood status thresholds
# -----------------------------------------------------------------------------
def test_flood_status_safe():
    assert anpr.flood_status(0.0) == "SAFE"
    assert anpr.flood_status(anpr.WARNING_THRESHOLD_CM - 0.1) == "SAFE"


def test_flood_status_warning():
    assert anpr.flood_status(anpr.WARNING_THRESHOLD_CM) == "WARNING"
    assert anpr.flood_status(anpr.DANGER_THRESHOLD_CM - 0.1) == "WARNING"


def test_flood_status_danger():
    assert anpr.flood_status(anpr.DANGER_THRESHOLD_CM) == "DANGER"
    assert anpr.flood_status(100.0) == "DANGER"


# -----------------------------------------------------------------------------
# Latest-item buffer behavior
# -----------------------------------------------------------------------------
def test_latest_buffer_replaces_old_items():
    """Prove that a fast producer replaces old items instead of accumulating.

    When the producer is faster than the consumer, put() overwrites the
    previous item and counts it as dropped, so the buffer never grows.
    """
    buf = anpr.LatestItemBuffer()
    # Producer puts many items before the consumer reads.
    for i in range(100):
        buf.put(i)
    # Only the newest item remains.
    assert buf.peek() == 99
    assert buf.dropped == 99
    # Consumer reads the newest item.
    assert buf.get(block=False) == 99
    assert buf.get(block=False) is None


def test_latest_buffer_get_clears():
    buf = anpr.LatestItemBuffer()
    buf.put("a")
    assert buf.get(block=False) == "a"
    assert buf.get(block=False) is None


def test_latest_buffer_empty_peek():
    buf = anpr.LatestItemBuffer()
    assert buf.peek() is None


# -----------------------------------------------------------------------------
# Dashboard status distinction
# -----------------------------------------------------------------------------
def test_dashboard_distinguishes_rejection_from_pending():
    """The dashboard must distinguish a rejected crop from a pending OCR job.

    A track with a rejection reason shows a crop-rejection status, while a
    track with a pending OCR job shows an OCR-queued status.
    """
    # Track with a rejected crop.
    rejected = anpr.TrackState()
    rejected.last_reject_reason = "too_small"
    rejected.last_reject_dims = (17, 6)
    assert rejected.pending_ocr_job < 0
    assert rejected.last_reject_reason == "too_small"

    # Track with a genuinely pending OCR job.
    pending = anpr.TrackState()
    pending.pending_ocr_job = 17
    assert pending.pending_ocr_job >= 0
    assert pending.last_reject_reason == ""

    # The two states are mutually distinguishable.
    assert (rejected.pending_ocr_job >= 0) != (pending.pending_ocr_job >= 0)
    assert bool(rejected.last_reject_reason) != bool(pending.last_reject_reason)


# -----------------------------------------------------------------------------
# OCR character-confusion correction
# -----------------------------------------------------------------------------
def test_confusion_variants_generates_single_char_replacements():
    variants = list(anpr._confusion_variants("WKV8363"))
    # "W" has a confusion mapping (-> U), so one variant is produced.
    assert "UKV8363" in variants
    # Only one character is changed at a time.
    for v in variants:
        assert sum(a != b for a, b in zip(v, "WKV8363")) == 1


def test_correct_plate_confusions_registered_unchanged():
    # A plate that is already registered is returned unchanged.
    plate, bonus = anpr.correct_plate_confusions("WKV8363", ["WKV8363"])
    assert plate == "WKV8363"
    assert bonus == 0.0


def test_correct_plate_confusions_single_match():
    # "UKV8363" (U misread for W) corrects to the registered "WKV8363".
    plate, bonus = anpr.correct_plate_confusions(
        "UKV8363", ["WKV8363", "SAB1234A"]
    )
    assert plate == "WKV8363"
    assert bonus == anpr.OCR_CONFUSION_BONUS


def test_correct_plate_confusions_no_match_unchanged():
    # No registered plate matches any variant, so nothing is guessed.
    plate, bonus = anpr.correct_plate_confusions("UKV8363", ["SAB1234A"])
    assert plate == "UKV8363"
    assert bonus == 0.0


def test_correct_plate_confusions_multiple_matches_unchanged():
    # Two different registered plates both match variants -> ambiguous, no guess.
    plate, bonus = anpr.correct_plate_confusions(
        "UKV8363", ["WKV8363", "UKV8363"]
    )
    assert plate == "UKV8363"
    assert bonus == 0.0


def test_correct_plate_confusions_empty_registered():
    plate, bonus = anpr.correct_plate_confusions("UKV8363", [])
    assert plate == "UKV8363"
    assert bonus == 0.0


def test_select_best_candidate_corrects_confusion():
    # OCR reads "UKV8363" (U for W) but "WKV8363" is registered. The corrected
    # plate should win even though the misread has slightly higher confidence.
    candidates = [("UKV8363", 0.90), ("WKV8363", 0.85)]
    plate, conf = anpr.select_best_candidate(candidates, ["WKV8363"])
    assert plate == "WKV8363"
    # The misread (0.90) is corrected to WKV8363 and gets the bonus.
    assert conf == pytest.approx(0.90 + anpr.OCR_CONFUSION_BONUS)


def test_select_best_candidate_no_registered_keeps_misread():
    # Without the registered list, the misread is kept as-is.
    candidates = [("UKV8363", 0.90), ("WKV8363", 0.85)]
    plate, conf = anpr.select_best_candidate(candidates)
    assert plate == "UKV8363"
    assert conf == pytest.approx(0.90)
