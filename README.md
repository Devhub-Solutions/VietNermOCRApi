# VNCV OCR + VietNerm — Web UI

Giao diện web cho OCR Scanner với WebSocket, SQLite DocType, và dark neon-lime UI.

## Cấu trúc thư mục

```
.
├── app.py              # FastAPI app (REST + WebSocket)
├── database.py         # SQLite helpers
├── ocr_app.db          # SQLite file (tự tạo khi chạy)
├── templates/
│   ├── index.html      # Giao diện Scanner chính
│   └── admin.html      # Quản lý DocType
└── static/             # (tùy chọn) static assets
```

## Cài đặt

```bash
pip install fastapi uvicorn jinja2 python-multipart vncv vietnerm
```

## Chạy

```bash
python app.py
# hoặc
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Mở trình duyệt tại: http://localhost:8000

## Tính năng

| Tính năng | Mô tả |
|---|---|
| **Scan Mode** | Upload ảnh, chọn DocType → OCR + NER |
| **History Mode** | Xem lại lịch sử các lần scan |
| **WebSocket** | Hiển thị tiến trình real-time (bước 1, 2, 3) |
| **SQLite DocType** | CRUD loại giấy tờ qua `/admin` |
| **REST API** | `/ocr/v1/scan`, `/api/doctypes`, `/api/history` |
| **API Docs** | Tự động tại `/docs` (Swagger) |

## API Endpoints

```
GET  /                         → Scanner UI
GET  /admin                    → Quản lý DocType
WS   /ws/scan                  → WebSocket tiến trình
POST /ocr/v1/scan?doc_type=... → OCR + NER
GET  /api/doctypes             → Danh sách doctype
POST /api/doctypes             → Thêm doctype
PATCH /api/doctypes/{id}       → Sửa doctype
DELETE /api/doctypes/{id}      → Xóa doctype
GET  /api/history              → Lịch sử scan
```

## Biến môi trường

```bash
DB_PATH=ocr_app.db   # Đường dẫn SQLite (mặc định: ocr_app.db)
```
