# model/

Reference-profile calibration for classification-service's
frequency-spectrum classifier (`../../../shared/spectrum_classifier.py`).
**No calibration has been done yet** -- `labels_config.json` is a
placeholder with an empty `classes` object, so the service runs in stub
mode until you fill it in. This is a much smaller ask than the ML
approach this project used to have: no training run, no GPU, no labeled
dataset of hundreds of images -- just a handful of reference photos per
part type.

## How the classifier works (context for calibration)

`shared/spectrum_classifier.extract_features()`: grayscale the image,
take its 2D FFT (`np.fft.fft2` + `fftshift`), compute the magnitude
spectrum, then sum energy into three radial frequency bands (low/mid/high,
as fractions of the spectrum's max radius) and normalize so the three
values sum to 1. `classify()` compares a new image's `[low, mid, high]`
vector against each configured class's `reference_features` by Euclidean
distance and picks the closest.

## Calibrating `labels_config.json`

1. Take several reference photos of each real part type, under roughly
   the conditions the actual worker/phone setup will use (lighting,
   distance, background) -- consistency matters more than quantity here.
2. For each photo, run:
   ```python
   from shared.spectrum_classifier import extract_features
   features = extract_features(open("bolt_sample1.jpg", "rb").read())
   ```
3. Average the `[low, mid, high]` vectors per class, and write them into
   `labels_config.json`:
   ```json
   {
     "classes": {
       "bolt": {"reference_features": [0.61, 0.29, 0.10]},
       "screw": {"reference_features": [0.55, 0.33, 0.12]}
     }
   }
   ```
4. Restart the service (or redeploy). `SpectrumClassifier` checks for any
   class with `reference_features` at startup, by config content alone --
   no separate flag to flip. As soon as at least one class is configured,
   stub mode turns off.

## The stub-mode honesty rule

Until step 4 above has actually happened, `POST /classify` MUST return
`{"label": "unclassified", "confidence": null, "stub": true, "reason":
"no reference spectrum profiles configured", "features": null}` -- never
a fabricated label dressed up as a real prediction. Same "pendiente"
discipline this repo's other reports use for unmeasured results (see
`THEORY/` and `LAB_TESTING/LAB1/`). Do not work around this by inventing
placeholder `reference_features` values just to make stub mode go away.

## Honesty note on verification

No reference photos of real parts exist in this environment, so
`labels_config.json` was never actually calibrated here -- only tested
with synthetic images of known dominant spatial frequency (see
`../../../shared/tests/test_spectrum_classifier.py`), which verify the
feature-extraction math is correct, not that any specific real bolt/nut/
screw/washer classification would be accurate.
