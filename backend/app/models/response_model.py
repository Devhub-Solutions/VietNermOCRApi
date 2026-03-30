from typing import Any

from pydantic import BaseModel, Field, model_validator


class OCRResult(BaseModel):
    doc_type: str = Field(..., description="Detected document type")
    raw_text: str = Field(..., description="OCR extracted text")
    fields: dict[str, Any] = Field(default_factory=dict, description="Structured entities")


class ProgressEvent(BaseModel):
    step: str
    progress: int | None = None


class OCRJsonRequest(BaseModel):
    image_base64: str | None = Field(default=None, description="Raw base64 or data URL")
    image_url: str | None = Field(default=None, description="HTTP/HTTPS URL to image or pdf")
    filename_hint: str | None = Field(default=None, description="Optional filename extension hint")
    session_id: str | None = Field(default=None, description="Socket session ID for streaming mode")

    @model_validator(mode="after")
    def validate_one_input(self):
        if not self.image_base64 and not self.image_url:
            raise ValueError("Either image_base64 or image_url must be provided")
        return self
