import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@sio.event
async def connect(sid, environ, auth):
    await sio.emit("progress", {"step": "connected", "progress": 0}, to=sid)


@sio.event
async def disconnect(sid):
    return None
