from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from socketio import ASGIApp

from .api.routes_ocr import router as ocr_router
from .socket.socket_manager import sio

fastapi_app = FastAPI(title="VietNerm OCR API", version="0.1.0")

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@fastapi_app.get("/health")
async def health_check():
    return {"status": "ok"}


fastapi_app.include_router(ocr_router)
app = ASGIApp(socketio_server=sio, other_asgi_app=fastapi_app)
