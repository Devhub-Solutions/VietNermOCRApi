from fastapi import FastAPI, UploadFile, File, HTTPException, Query, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import tempfile, os, json, asyncio
from database import (
    init_db, get_all_doctypes, get_enabled_doctypes,
    add_doctype, update_doctype, delete_doctype,
    save_scan_history, get_scan_history
)
from huggingface_hub import HfApi, snapshot_download, scan_cache_dir
import shutil

# ── OCR / NER imports — đúng pattern gốc ──────────────────────────────────────
try:
    from vncv.ocr import extract_text
    from vietnerm import VietNerm
    from vietnerm.download import DownloadConfig

    config = DownloadConfig(disable_ssl_verify=True)
    config.apply_environment()

    ner = VietNerm(download_config=config)
    OCR_AVAILABLE = True
    print("[INFO] VietNerm loaded OK")
except Exception as e:
    OCR_AVAILABLE = False
    print(f"[WARN] OCR/NER not available: {e}")

# ── App setup ──────────────────────────────────────────────────────────────────
app = FastAPI(title="VNCV OCR + VietNerm API")
templates = Jinja2Templates(directory="templates")

if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_event():
    init_db()

# ── WebSocket manager ──────────────────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def send(self, ws: WebSocket, data: dict):
        await ws.send_text(json.dumps(data, ensure_ascii=False))

manager = ConnectionManager()

# ── Helpers ────────────────────────────────────────────────────────────────────
def save_temp_file(file: UploadFile) -> str:
    suffix = os.path.splitext(file.filename)[1] or ".jpg"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        content = file.file.read()
        tmp.write(content)
        tmp.flush()
        return tmp.name
    finally:
        tmp.close()

# ── Pydantic models ────────────────────────────────────────────────────────────
class OcrNerResponse(BaseModel):
    success: bool
    doc_type: str
    raw_text: str
    ner_result: Dict[str, Any]

class DoctypeCreate(BaseModel):
    key: str
    label: str
    aliases: str = ""
    enabled: bool = True

class DoctypeUpdate(BaseModel):
    label: Optional[str] = None
    aliases: Optional[str] = None
    enabled: Optional[bool] = None

# ══════════════════════════════════════════════════════════════════════════════
# UI ROUTES
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    doctypes = get_enabled_doctypes()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "doctypes": doctypes,
        "ocr_available": OCR_AVAILABLE,
    })

@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    doctypes = get_all_doctypes()
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "doctypes": doctypes,
    })
@app.get("/guide", response_class=HTMLResponse)
async def guide(request: Request):
    return templates.TemplateResponse("guide.html", {
        "request": request,
    })
# ══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET
# ══════════════════════════════════════════════════════════════════════════════
@app.websocket("/ws/scan")
async def websocket_scan(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            if msg.get("action") == "ping":
                await manager.send(websocket, {"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ══════════════════════════════════════════════════════════════════════════════
# OCR SCAN
# ══════════════════════════════════════════════════════════════════════════════
@app.post("/ocr/v1/scan", response_model=OcrNerResponse)
async def scan_image(
    file: UploadFile = File(...),
    doc_type: str = Query("cccd", description="Loai giay to"),
    ws_id: Optional[str] = Query(None)
):
    if not OCR_AVAILABLE:
        raise HTTPException(status_code=503, detail="OCR engine not available.")
    try:
        # 1. Luu anh tam
        temp_path = save_temp_file(file)

        for ws in manager.active:
            await manager.send(ws, {"type": "progress", "step": 1, "msg": "Dang trich xuat van ban..."})

        # 2. OCR
        text = extract_text(temp_path)
        rawtext = "\n".join(text)

        for ws in manager.active:
            await manager.send(ws, {"type": "progress", "step": 2, "msg": "Dang nhan dang thuc the (NER)..."})

        # 3. NER
        result = ner.extract(doc_type=doc_type, text=rawtext)

        try:
            os.remove(temp_path)
        except OSError:
            pass

        for ws in manager.active:
            await manager.send(ws, {
                "type": "done", "step": 3, "msg": "Hoan tat!",
                "doc_type": doc_type, "raw_text": rawtext, "ner_result": result,
            })

        save_scan_history(doc_type, file.filename, rawtext, json.dumps(result, ensure_ascii=False), True)

        return {"success": True, "doc_type": doc_type, "raw_text": rawtext, "ner_result": result}

    except HTTPException:
        raise
    except Exception as e:
        for ws in manager.active:
            await manager.send(ws, {"type": "error", "msg": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

# ══════════════════════════════════════════════════════════════════════════════
# DOCTYPE CRUD
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/api/doctypes")
async def api_list_doctypes(enabled_only: bool = Query(False)):
    return get_enabled_doctypes() if enabled_only else get_all_doctypes()

@app.post("/api/doctypes", status_code=201)
async def api_add_doctype(body: DoctypeCreate):
    try:
        return add_doctype(body.key, body.label, body.aliases, body.enabled)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.patch("/api/doctypes/{doctype_id}")
async def api_update_doctype(doctype_id: int, body: DoctypeUpdate):
    update_doctype(doctype_id, body.label, body.aliases, body.enabled)
    return {"ok": True}

@app.delete("/api/doctypes/{doctype_id}")
async def api_delete_doctype(doctype_id: int):
    delete_doctype(doctype_id)
    return {"ok": True}

# ══════════════════════════════════════════════════════════════════════════════
# MODEL MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════
HF_REPO_PREFIX = "ngocthanhdoan/"

@app.get("/api/models")
async def list_models():
    """Liệt kê các model hiện có trong cache và phiên bản mới nhất trên HF"""
    try:
        hf_api = HfApi()
        doctypes = get_all_doctypes()
        results = []
        
        # Scan local cache
        cache_info = scan_cache_dir()
        local_models = {}
        for repo in cache_info.repos:
            if repo.repo_id.startswith(HF_REPO_PREFIX):
                # Lấy revision mới nhất trong cache
                latest_revision = sorted(repo.revisions, key=lambda x: x.last_modified, reverse=True)[0]
                local_models[repo.repo_id] = {
                    "commit_hash": latest_revision.commit_hash,
                    "last_modified": latest_revision.last_modified.isoformat()
                }

        for dt in doctypes:
            repo_id = f"{HF_REPO_PREFIX}{dt['key']}"
            model_info = {
                "id": dt['id'],
                "key": dt['key'],
                "label": dt['label'],
                "repo_id": repo_id,
                "local": local_models.get(repo_id),
                "remote": None,
                "update_available": False
            }
            
            try:
                remote_info = hf_api.model_info(repo_id)
                model_info["remote"] = {
                    "commit_hash": remote_info.sha,
                }
                if model_info["local"]:
                    model_info["update_available"] = model_info["local"]["commit_hash"] != remote_info.sha
                else:
                    model_info["update_available"] = True
            except Exception:
                pass # Model không tồn tại trên HF
                
            results.append(model_info)
            
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/models/{key}/update")
async def update_model(key: str):
    """Tải hoặc cập nhật model từ HF"""
    repo_id = f"{HF_REPO_PREFIX}{key}"
    try:
        # Xóa cache cũ nếu có để đảm bảo tải mới nhất (theo yêu cầu xóa model cũ tải model mới)
        cache_info = scan_cache_dir()
        for repo in cache_info.repos:
            if repo.repo_id == repo_id:
                # Xóa toàn bộ repo trong cache
                shutil.rmtree(repo.repo_path)
                break
        
        # Tải mới
        snapshot_download(repo_id=repo_id)
        return {"success": True, "message": f"Model {key} updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/models/{key}")
async def delete_model_cache(key: str):
    """Xóa model khỏi cache local"""
    repo_id = f"{HF_REPO_PREFIX}{key}"
    try:
        cache_info = scan_cache_dir()
        deleted = False
        for repo in cache_info.repos:
            if repo.repo_id == repo_id:
                shutil.rmtree(repo.repo_path)
                deleted = True
                break
        return {"success": deleted, "message": f"Model {key} cache deleted" if deleted else "Model not found in cache"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ══════════════════════════════════════════════════════════════════════════════
# HISTORY
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/api/history")
async def api_history(limit: int = Query(20)):
    return get_scan_history(limit)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)