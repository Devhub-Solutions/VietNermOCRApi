class DocTypeService:
    """Document type detector with optional vietnerm backend."""

    def detect(self, raw_text: str) -> str:
        try:
            from vietnerm import DocTypeDetector  # type: ignore

            detector = DocTypeDetector()
            detection = detector.detect(raw_text)
            return getattr(detection, "doc_type", "UNKNOWN")
        except Exception:
            upper_text = raw_text.upper()
            if "RA VIEN" in upper_text or "XUAT VIEN" in upper_text:
                return "GIAY_RA_VIEN"
            if "CCCD" in upper_text or "CAN CUOC" in upper_text:
                return "CCCD"
            return "UNKNOWN"
