# Next step after training (not implemented here)

Once `train.py` finishes, `training/runs/parts_sorting/weights/best.pt` holds the trained model.

- For a quick local-server integration later, the `.pt` file can be loaded directly with `ultralytics.YOLO(path)` — simplest, but it pulls the full `ultralytics`/`torch` stack into the server's runtime.
- For a lighter-weight runtime (no torch dependency in local-server), export to ONNX instead: `model.export(format="onnx")` (produces `best.onnx` next to `best.pt`). This still needs an ONNX runtime inference call written on the server side.
- Either file would need to be dropped into `LOCAL_MODE/local-server/model/` (same folder the existing non-ML classifier currently uses) for the server to pick it up — but wiring that consumption into `app/main.py` / `shared/spectrum_classifier.py` is a separate task, intentionally NOT done by this training pipeline.
- Not verified: which format (`.pt` vs `.onnx`) the eventual server integration will prefer — that decision belongs to whoever implements the server-side consumption.
