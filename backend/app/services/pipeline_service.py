from ..models.response_model import OCRResult
from ..socket.socket_manager import sio
from .doctype_service import DocTypeService
from .ner_service import NERService
from .ocr_service import OCRService


class OCRPipeline:
    def __init__(self) -> None:
        self.ocr = OCRService()
        self.doctype = DocTypeService()
        self.ner = NERService()

    def run(self, image_path: str) -> OCRResult:
        raw_text = self.ocr.extract_text(image_path)
        doc_type = self.doctype.detect(raw_text)
        fields = self.ner.extract(doc_type=doc_type, text=raw_text)
        return OCRResult(doc_type=doc_type, raw_text=raw_text, fields=fields)

    async def run_stream(self, image_path: str, session_id: str) -> OCRResult:
        await sio.emit("progress", {"step": "OCR running", "progress": 25}, to=session_id)
        raw_text = self.ocr.extract_text(image_path)

        await sio.emit(
            "progress", {"step": "Detecting document type", "progress": 60}, to=session_id
        )
        doc_type = self.doctype.detect(raw_text)

        await sio.emit("progress", {"step": "Extracting NER", "progress": 85}, to=session_id)
        fields = self.ner.extract(doc_type=doc_type, text=raw_text)

        result = OCRResult(doc_type=doc_type, raw_text=raw_text, fields=fields)
        await sio.emit("result", result.model_dump(), to=session_id)
        return result
