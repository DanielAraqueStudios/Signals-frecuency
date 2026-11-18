"""Part-diameter measurement from a reference marker, independent of the
YOLO classification pipeline (which only identifies part TYPE, not size).

Approach (as specified by the project owner):
  1. Threshold the image to isolate black pixels -- the calibration marker,
     a single straight black line/strip of known physical length = 1cm,
     placed in the same photo as the part on a light/contrasting background.
  2. Find all black contours; because edge/contour detection on one real
     marker can yield several slightly different pixel-length readings
     (anti-aliasing, partial occlusion, noise), every candidate marker
     segment's pixel length is averaged into a single `pixels_per_cm`
     calibration value (the marker is defined as exactly 1cm, so the
     averaged pixel length *is* pixels_per_cm).
  3. Separately find the part's own contour and measure its width/diameter
     in pixels (via the minimum-area rectangle's shorter side), then
     convert to cm using that calibration value.

Marker vs. part heuristic (documented assumption): the marker is thin and
black; the part is a larger, roughly round/solid, mid-tone (metallic/gray)
object -- distinctly brighter than the black marker but still darker than
the light/contrasting background it sits on. Marker candidates come from
thresholding for dark pixels and keeping only contours whose minAreaRect
long/short side ratio exceeds MARKER_MIN_ASPECT_RATIO (thin and elongated,
not a blob). The part is taken as the largest contour in a separate
mid-tone band (darker than WHITE_THRESHOLD, brighter than BLACK_THRESHOLD),
which excludes both the marker and the background. This is a heuristic,
not a general solution -- it assumes the marker is the only black object in
frame and the part is neither black nor as bright as the background.

Never raises on bad/ambiguous input: mirrors this project's stub-response
house style (see shared/spectrum_classifier.py and app/store.py) -- every
failure path returns a dict with `diameter_cm: None` and a `reason` string
instead of propagating an exception.
"""

from __future__ import annotations

import cv2
import numpy as np

# Pixels are "black" below this per-channel grayscale intensity.
BLACK_THRESHOLD = 60

# A contour is a marker candidate if its minAreaRect long/short side ratio
# exceeds this (i.e. thin and elongated, not a blob).
MARKER_MIN_ASPECT_RATIO = 3.0

# Pixels brighter than this are the light/contrasting background, not the
# part -- the part is assumed to be a mid-tone (metallic/gray) object that
# is neither as dark as the black marker nor as bright as the background.
WHITE_THRESHOLD = 200

# Ignore tiny noise specks when finding contours.
MIN_CONTOUR_AREA = 20.0


def _rect_dims(contour: np.ndarray) -> tuple[float, float]:
    (_, _), (w, h), _ = cv2.minAreaRect(contour)
    return (w, h) if w >= h else (h, w)


def measure_diameter_cm(image_bytes: bytes) -> dict:
    """Measure a part's diameter in cm using a 1cm black reference marker
    in the same frame. Never raises -- returns a dict with `reason` set on
    any failure to find a marker or a part."""
    failure = {
        "diameter_cm": None,
        "pixels_per_cm": None,
        "marker_segments_found": 0,
        "confidence": None,
        "reason": None,
    }

    try:
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception as exc:  # pragma: no cover - defensive, imdecode rarely raises
        failure["reason"] = f"failed to decode image: {exc}"
        return failure

    if image is None:
        failure["reason"] = "failed to decode image: not a valid image"
        return failure

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, black_mask = cv2.threshold(gray, BLACK_THRESHOLD, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) >= MIN_CONTOUR_AREA]

    marker_lengths: list[float] = []
    for c in contours:
        long_side, short_side = _rect_dims(c)
        if short_side <= 0:
            continue
        aspect_ratio = long_side / short_side
        if aspect_ratio >= MARKER_MIN_ASPECT_RATIO:
            marker_lengths.append(long_side)

    if not marker_lengths:
        failure["reason"] = "no reference marker found (no thin black contour detected)"
        return failure

    pixels_per_cm = float(np.mean(marker_lengths))
    if pixels_per_cm <= 0:
        failure["reason"] = "degenerate marker measurement (zero-length segment)"
        return failure

    # Part candidates: larger blobs that are NOT black (metallic/gray part,
    # not the black marker) and not already classified as marker segments.
    all_contours, _ = cv2.findContours(
        _part_mask(gray),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    part_candidates = [c for c in all_contours if cv2.contourArea(c) >= MIN_CONTOUR_AREA]

    if not part_candidates:
        failure["marker_segments_found"] = len(marker_lengths)
        failure["pixels_per_cm"] = pixels_per_cm
        failure["reason"] = "no part contour found (no non-black object detected)"
        return failure

    part_contour = max(part_candidates, key=cv2.contourArea)
    long_side, short_side = _rect_dims(part_contour)
    diameter_pixels = short_side

    diameter_cm = diameter_pixels / pixels_per_cm

    return {
        "diameter_cm": diameter_cm,
        "pixels_per_cm": pixels_per_cm,
        "marker_segments_found": len(marker_lengths),
        "confidence": "stub" if len(marker_lengths) < 2 else "ok",
        "reason": None,
    }


def _part_mask(gray: np.ndarray) -> np.ndarray:
    """Mid-tone pixels only: excludes the black marker and the light
    background, isolating the (metallic/gray) part."""
    return cv2.inRange(gray, BLACK_THRESHOLD, WHITE_THRESHOLD)
