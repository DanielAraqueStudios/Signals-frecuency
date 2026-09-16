FROM python:3.12-slim

WORKDIR /app

# Build context is PARTS_SORTING_PLATFORM/ (the repo root shared by both
# deployment modes), not this folder -- see ../docker-compose.yml -- so
# services/shared/spectrum_classifier.py can be copied into the image.
COPY CLOUD_MODE/classification-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY CLOUD_MODE/classification-service/app ./app
COPY CLOUD_MODE/classification-service/model/labels_config.json ./model/labels_config.json
COPY shared ./shared

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
