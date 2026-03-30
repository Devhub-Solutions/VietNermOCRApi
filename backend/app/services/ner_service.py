from typing import Any


class NERService:
    """Named entity extraction with optional vietnerm backend."""

    def extract(self, doc_type: str, text: str) -> dict[str, Any]:
        try:
            from vietnerm import VietNerm  # type: ignore

            ner = VietNerm()
            result = ner.extract(doc_type=doc_type, text=text)
            if isinstance(result, dict):
                return result
            return {"raw_result": str(result)}
        except Exception:
            preview = text[:140].replace("\n", " ")
            return {
                "document_type": doc_type,
                "text_preview": preview,
                "note": "vietnerm is not installed; this is fallback output",
            }
