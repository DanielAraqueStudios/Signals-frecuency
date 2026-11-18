# Training a YOLO detector for brocas / escariadores / tornillos

This replaces the non-ML 2D-FFT spectrum classifier with a real object detector,
trained from scratch (no pretrained weights for these specific parts exist — we
start from a generic `yolov8n.pt` checkpoint and fine-tune it on our own photos).

This is a standalone, optional pipeline. It does **not** run as part of the
FastAPI server and has its own dependency file (`requirements-training.txt`) —
install it separately, in its own virtualenv if you can, since `ultralytics`
pulls in `torch` (large, and GPU-accelerated if you have a CUDA GPU).

## 1. How many photos do you actually need?

Honest minimums for 3 simple, rigid, visually distinct classes (drill bits,
reamers, screws) photographed from a fixed overhead angle:

- **~150-300 images per class** to get a first usable model (roughly 450-900 total).
- Below ~100/class, expect the model to overfit badly and fail on anything but
  near-identical lighting/poses to training data.
- More matters more than fancier tricks — if the first model performs poorly,
  the fix is almost always "collect more varied images," not "tune hyperparameters."
- Each image can (and should) contain several parts at once, each with its own
  box — that's "free" extra training signal per photo.

## 2. Capturing images on this rig

- Mount the phone at a **fixed height and angle** over the conveyor band — consistency
  across photos matters more than any single "ideal" angle.
- **Stop the band during capture.** A moving band under phone-camera exposure will
  motion-blur the parts, which hurts both your labeling accuracy and the model.
- Light consistently from above; avoid harsh shadows or glare that change
  between sessions — the lighting during inference should resemble the lighting
  used for training as closely as possible.
- Vary what you *can* control between shots: part orientation/rotation, position
  on the band, how many parts are in frame and whether they touch/overlap,
  and (if feasible) different individual pieces of the same part type (wear,
  size variation) rather than photographing the same single screw 300 times.
- Keep background and band surface the same between training and the real
  deployment setup — the model will learn background texture as a cue whether
  you want it to or not.

## 3. Labeling

Draw a bounding box around each part and assign it a class. Recommended tools
(pick whichever is easiest to get running):

- [Label Studio](https://labelstud.io/) — full-featured, runs locally or via Docker.
- [makesense.ai](https://www.makesense.ai/) — free, browser-only, no install, exports YOLO format directly.
- [`labelImg`](https://github.com/HumanSignal/labelImg) — lightweight desktop tool, long-standing default for YOLO labeling.

### YOLO label format

Each image `foo.jpg` gets a matching `foo.txt` with **one line per object**:

```
<class-id> <x_center> <y_center> <width> <height>
```

- `class-id` is `0` = `brocas`, `1` = `escariadores`, `2` = `tornillos` (must match `data.yaml`).
- All four numbers after the class id are **normalized to 0-1** (divide pixel
  values by image width/height), and are `x_center y_center width height` of
  the box — not corner coordinates.
- An image with no objects in it simply has no matching `.txt` file (or an empty one).

Most labeling tools above can export directly in this format — look for a
"YOLO" export option rather than hand-writing these files.

## 4. Folder layout and train/val split

Put labeled data into:

```
training/dataset/images/train/*.jpg
training/dataset/images/val/*.jpg
training/dataset/labels/train/*.txt   # same basename as the matching image
training/dataset/labels/val/*.txt
```

Split roughly **85% train / 15% val**, shuffled, not grouped by capture session
(otherwise val performance will look artificially good or bad depending on
which session you held out). `data.yaml` already points at these folders.

## 5. Running training

```bash
pip install -r requirements-training.txt
python train.py
```

Defaults (overridable via CLI flags — see `train.py --help`):

- `--epochs 100` with `--patience 20` (stops early if validation stops improving)
- `--imgsz 640`
- `--batch 16`
- starts from `yolov8n.pt` (smallest/fastest YOLOv8 variant — appropriate
  given we only have a few hundred images per class; a bigger backbone would
  overfit faster on a dataset this size)

Best weights land at `training/runs/parts_sorting/weights/best.pt`.

**Not verified**: exact Ultralytics `YOLO.train()` argument names/behavior for
`patience`, `batch=-1` (auto-batch), and the default run output path can shift
between `ultralytics` versions — if `train.py` errors on an unrecognized
argument, check `pip show ultralytics` against the pinned version in
`requirements-training.txt` and consult the installed version's own `--help`
or docs rather than assuming this README is still accurate.

## 6. After training

See `export_and_wire.md` for the (not-yet-implemented) next step of getting
the trained model into the local-server.
