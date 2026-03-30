# VietNerm OCR API (FastAPI + Socket.IO + Frontend Demo)

Dự án mẫu để chạy pipeline **OCR → DocType Detection → NER** theo thời gian thực.

## Kiến trúc

- Backend: FastAPI + python-socketio
- Frontend: static HTML + Socket.IO client
- Pipeline: `OCRService` → `DocTypeService` → `NERService`
- Input hỗ trợ: multipart file, JSON base64, JSON image URL

## Cấu trúc

```text
backend/
  app/
    api/routes_ocr.py
    main.py
    models/response_model.py
    services/
      ocr_service.py
      doctype_service.py
      ner_service.py
      pipeline_service.py
    socket/socket_manager.py
    utils/image_loader.py
  Dockerfile
  requirements.txt
frontend/
  Dockerfile
  index.html
docker-compose.yml
```

## Chạy bằng Docker

```bash
docker compose up --build
```

- Backend API: `http://localhost:8000`
- Frontend demo: `http://localhost:5500`

## Chạy local không Docker

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

```bash
cd frontend
python -m http.server 5500
```

## API

- `GET /health`
- `POST /api/ocr` (multipart: `file`)
- `POST /api/ocr/stream` (multipart: `file`, `session_id`)
- `POST /api/ocr/json` (json: `image_base64` hoặc `image_url`, optional `session_id`)

### Ví dụ JSON base64

```json
{
  "image_base64": "data:image/png;base64,iVBORw0KGgo...",
  "session_id": "socket-id"
}
```

### Ví dụ JSON image URL

```json
{
  "image_url": "https://example.com/document.jpg",
  "session_id": "socket-id"
}
```

## Ghi chú tích hợp thật

Nếu đã cài `vncv` và `vietnerm`, service sẽ tự dùng model thật.
Nếu chưa có, code fallback để giúp bạn test end-to-end luồng API và Socket.IO.
