import base64
from pathlib import Path
from tempfile import NamedTemporaryFile

import httpx


def save_bytes_to_tempfile(content: bytes, suffix: str = ".bin") -> Path:
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        return Path(tmp.name)


def decode_base64_to_file(data: str, filename_hint: str | None = None) -> Path:
    payload = data.split(",", 1)[1] if data.startswith("data:") else data
    content = base64.b64decode(payload)
    suffix = Path(filename_hint).suffix if filename_hint else ".bin"
    if not suffix:
        suffix = ".bin"
    return save_bytes_to_tempfile(content=content, suffix=suffix)


async def download_url_to_file(url: str) -> Path:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(url)
        response.raise_for_status()
    suffix = Path(url).suffix or ".bin"
    return save_bytes_to_tempfile(content=response.content, suffix=suffix)
