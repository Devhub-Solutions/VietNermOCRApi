from pathlib import Path


class OCRService:
    """Wrapper for OCR extraction.

    Uses vncv when available, otherwise returns placeholder text so local setup still runs.
    """

    def extract_text(self, image_path: str) -> str:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            from vncv.ocr import extract_text  # type: ignore

            lines = extract_text(str(path))
            if isinstance(lines, list):
                return "\n".join(str(line) for line in lines)
            return str(lines)
        except Exception:
            return f"[OCR fallback] file={path.name}"
