"""Unit tests for the Malaysian ANPR pipeline pure functions and state logic.

These tests require no camera, Supabase, serial port, YOLO weights, PaddleOCR
model downloads, CUDA, or internet access. They use mocks and pure functions.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Make the module under test importable without triggering heavy optional
# dependencies (cv2 is required; YOLO/PaddleOCR are optional and guarded).
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
def test_select_best_candidate_v2_style():
    # PaddleOCR 2.x style: list of [box, (text, score)]
    raw = [
        [[0, 0, 10, 10], ("WKV8363", 0.91)],
        [[0, 0, 10, 10], ("TOYOTA", 0.99)],
    ]
    candidates = []
    anpr._collect_ocr_candidates(raw, candidates)
    text, conf = anpr.select_best_candidate(candidates)
    assert text == "WKV8363"
    assert conf == pytest.approx(0.91)


def test_select_best_candidate_v3_style():
    # PaddleOCR 3.x style: dict with rec_texts / rec_scores
    raw = {"rec_texts": ["WKV8363", "MAL"], "rec_scores": [0.88, 0.99]}
    candidates = []
    anpr._collect_ocr_candidates(raw, candidates)
    text, conf = anpr.select_best_candidate(candidates)
    assert text == "WKV8363"
    assert conf == pytest.approx(0.88)


def test_select_best_candidate_one_valid():
    candidates = [("WKV8363", 0.9, 0), ("GARBAGE", 0.99, 1)]
    text, conf = anpr.select_best_candidate(candidates)
    assert text == "WKV8363"
    assert conf == pytest.approx(0.9)


def test_select_best_candidate_highest_confidence_wins():
    candidates = [("WKV8363", 0.7, 0), ("SAB1234A", 0.95, 1)]
    text, conf = anpr.select_best_candidate(candidates)
    assert text == "SAB1234A"
    assert conf == pytest.approx(0.95)


def test_select_best_candidate_dedup_normalized():
    candidates = [("WKV 8363", 0.7, 0), ("WKV8363", 0.95, 1)]
    text, conf = anpr.select_best_candidate(candidates)
    assert text == "WKV8363"
    assert conf == pytest.approx(0.95)


def test_select_best_candidate_empty():
    assert anpr.select_best_candidate([]) == ("", 0.0)


def test_select_best_candidate_malformed():
    candidates = [("WKV8363", "not-a-number", 0), (None, 0.5, 1)]
    text, conf = anpr.select_best_candidate(candidates)
    assert text == ""
    assert conf == 0.0


def test_candidates_never_concatenated():
    # Two valid candidates must NOT be joined into one string.
    candidates = [("WKV", 0.9, 0), ("8363", 0.9, 1)]
    text, _ = anpr.select_best_candidate(candidates)
    assert text != "WKV8363"
    assert text == ""  # neither is a valid full plate


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
    assert state.confirmed_samples == 7


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
    # Both have 2 votes; tie-break by confidence then lexicographic.
    winner = state.provisional_text
    assert winner in ("WKV8363", "SAB1234A")
    # Running again must give the same result.
    state2 = anpr.TrackState()
    for text in ["WKV8363", "SAB1234A", "WKV8363", "SAB1234A"]:
        state2.add_reading(text, 0.9)
    assert state2.provisional_text == winner


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
    # Add sharp edges.
    crop[40:60, 40:160] = 30
    result = anpr.evaluate_crop_quality(crop)
    assert result["accepted"] is True
    assert result["reason"] == ""
    assert result["width"] == 200
    assert result["height"] == 100


# -----------------------------------------------------------------------------
# Preprocessing variants
# -----------------------------------------------------------------------------
def test_variants_invalid_crop_returns_empty():
    assert anpr.make_plate_variants(None) == []
    assert anpr.make_plate_variants(np.zeros((0, 0, 3), dtype=np.uint8)) == []


def test_variants_original_preserves_color():
    crop = np.zeros((50, 100, 3), dtype=np.uint8)
    crop[:, :, 0] = 255  # blue channel
    variants = anpr.make_plate_variants(crop)
    names = [name for name, _ in variants]
    assert names == ["original", "gray", "clahe"]
    original = variants[0][1]
    assert original.shape == (50, 100, 3)
    assert original.dtype == np.uint8


def test_variants_gray_and_clahe_are_bgr():
    crop = np.zeros((50, 100, 3), dtype=np.uint8)
    variants = anpr.make_plate_variants(crop)
    for name, image in variants:
        assert len(image.shape) == 3, f"{name} not 3-channel"
        assert image.shape[2] == 3, f"{name} not BGR"


def test_variants_upscaled_dimensions():
    crop = np.zeros((50, 100, 3), dtype=np.uint8)
    variants = anpr.make_plate_variants(crop)
    gray = dict(variants)["gray"]
    clahe = dict(variants)["clahe"]
    expected_h = 50 * anpr.OCR_UPSCALE
    expected_w = 100 * anpr.OCR_UPSCALE
    assert gray.shape[:2] == (expected_h, expected_w)
    assert clahe.shape[:2] == (expected_h, expected_w)


def test_variant_names_stable():
    crop = np.zeros((50, 100, 3), dtype=np.uint8)
    variants = anpr.make_plate_variants(crop)
    assert [name for name, _ in variants] == ["original", "gray", "clahe"]


# -----------------------------------------------------------------------------
# recognize_best_variant with mocked OCR engine
# -----------------------------------------------------------------------------
class _MockEngine:
    def __init__(self, results_by_variant):
        self.results_by_variant = results_by_variant
        self.calls = []

    def predict(self, image):
        # Identify variant by shape to simulate per-variant results.
        h, w = image.shape[:2]
        key = "original" if (h, w) == (50, 100) else "upscaled"
        self.calls.append(key)
        return self.results_by_variant.get(key, [])


def test_recognize_best_variant_selects_highest():
    engine = _MockEngine(
        {
            "original": [{"rec_texts": ["WKV8363"], "rec_scores": [0.7]}],
            "upscaled": [{"rec_texts": ["SAB1234A"], "rec_scores": [0.95]}],
        }
    )
    crop = np.zeros((50, 100, 3), dtype=np.uint8)
    text, conf, variant = anpr.recognize_best_variant(engine, crop)
    assert text == "SAB1234A"
    assert conf == pytest.approx(0.95)
    assert variant == "gray" or variant == "clahe"


def test_recognize_best_variant_all_fail():
    engine = _MockEngine({})
    crop = np.zeros((50, 100, 3), dtype=np.uint8)
    text, conf, variant = anpr.recognize_best_variant(engine, crop)
    assert text == ""
    assert conf == 0.0
    assert variant == ""
