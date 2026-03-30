from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, Form, UploadFile

from ..models.response_model import OCRJsonRequest
from ..services.pipeline_service import OCRPipeline
from ..utils.image_loader import decode_base64_to_file, download_url_to_file

router = APIRouter(prefix="/api", tags=["ocr"])
pipeline = OCRPipeline()


def _save_upload(file: UploadFile) -> Path:
    suffix = Path(file.filename or "upload.bin").suffix
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file.file.read())
        return Path(tmp.name)


@router.post("/ocr")
async def process_ocr(file: UploadFile = File(...)):
    image_path = _save_upload(file)
    try:
        return pipeline.run(str(image_path))
    finally:
        image_path.unlink(missing_ok=True)


@router.post("/ocr/stream")
async def process_ocr_stream(file: UploadFile = File(...), session_id: str = Form(...)):
    image_path = _save_upload(file)
    try:
        return await pipeline.run_stream(str(image_path), session_id=session_id)
    finally:
        image_path.unlink(missing_ok=True)


@router.post("/ocr/json")
async def process_ocr_json(payload: OCRJsonRequest):
    image_path = (
        decode_base64_to_file(payload.image_base64, payload.filename_hint)
        if payload.image_base64
        else await download_url_to_file(payload.image_url or "")
    )

    try:
        if payload.session_id:
            return await pipeline.run_stream(str(image_path), session_id=payload.session_id)
        return pipeline.run(str(image_path))
    finally:
        image_path.unlink(missing_ok=True)
