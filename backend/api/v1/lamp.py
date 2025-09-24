# api/v1/lamp.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

router = APIRouter()

# Global variable to hold the current WebSocket connection from Unity.
unity_ws = None

class LampCommand(BaseModel):
    state: str  # Expected values: "on" or "off"

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global unity_ws
    await websocket.accept()
    unity_ws = websocket
    try:
        while True:
            # Listen for any incoming messages from Unity (for debugging or acknowledgments).
            data = await websocket.receive_text()
            print(f"Received from Unity: {data}")
    except WebSocketDisconnect:
        print("Unity disconnected")
        unity_ws = None

@router.post("/lamp")
async def toggle_lamp(command: LampCommand):
    global unity_ws
    if unity_ws is None:
        return {"error": "Unity client not connected"}
    
    # Format the command in a way Unity can parse.
    message = f"lamp:{command.state}"
    await unity_ws.send_text(message)
    return {"message": "Command sent", "command": message}
