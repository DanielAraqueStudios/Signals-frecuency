# model/

Training pipeline for classification-service. **No labeled dataset
exists yet**, so this directory currently produces nothing at rest --
`weights/` only holds a `.gitkeep`, and the service runs in stub mode
until you run this pipeline yourself. See `../app/infer.py` and the
service `README.md`'s "Stub mode" section for what stub mode returns.

## Two-environment split

The serving container (`../Dockerfile`, `../requirements.txt`) installs
`onnxruntime` only -- it runs a pre-exported `.onnx` file, never a live
PyTorch/TF graph. Training needs `torch` and `torchvision`, which are
**not** in `../requirements.txt` (they'd bloat the serving image and
Railway has no GPU tier to justify shipping them there anyway). Install
them yourself in a separate environment before running the scripts below:

```bash
pip install torch==2.4.1 torchvision==0.19.1 onnx==1.16.2
```

## From a labeled `data/` folder to `model/weights/model.onnx`

1. **Replace `labels.json`'s placeholder class list** with your real
   part classes -- or just run `train.py`, which rewrites `labels.json`
   from your `data/` subfolder names automatically (alphabetical order,
   matching how `torchvision.datasets.ImageFolder` assigns label indices).
2. **Collect images**: `data/<class_name>/*.jpg`, one subfolder per part
   type (e.g. `data/bolt/`, `data/screw/`, `data/nut/`, `data/washer/`).
   A few dozen images per class is enough to fine-tune the MobileNetV2
   head.
3. **Train**: `python train.py --data-dir data --epochs 10 --out
   model/checkpoint.pt` -- fine-tunes an ImageNet-pretrained MobileNetV2
   with a new classifier head sized to your class count, prints per-epoch
   train loss / val accuracy, saves the checkpoint.
4. **Export + quantize**: `python export_onnx.py --checkpoint
   model/checkpoint.pt --out model/weights/model.onnx` -- exports to ONNX
   then INT8-quantizes it via `onnxruntime.quantization.quantize_dynamic`.
5. **Restart the service** (or deploy). `app/infer.py` checks for
   `model/weights/model.onnx` at startup by file presence alone -- no
   config flag to flip. As soon as the file exists, stub mode turns off
   and `/classify` returns real predictions.

## The stub-mode honesty rule

Until step 5 above has actually happened, `POST /classify` MUST return
`{"label": "unclassified", "confidence": null, "stub": true, "reason":
"no trained model present"}` -- never a fabricated label dressed up as a
real prediction. This is the same "pendiente" discipline this repo's
other reports use for unmeasured results (see `THEORY/` and
`LAB_TESTING/LAB1/`). Do not work around this by shipping a randomly
initialized or otherwise untrained `.onnx` file just to make stub mode
go away -- that would be a fabricated result, which is exactly what this
rule exists to prevent.

## Honesty note on verification

`train.py` and `export_onnx.py` were written to be correct, runnable
Python, but were **not run end-to-end** in the environment this was
built in -- there is no labeled image dataset yet, and installing
`torch`/`torchvision` there was not attempted (see the service
`README.md`'s verification section for exactly what *was* run: the
stub-mode inference/API tests, which do not need torch).
