# backend/api/v1/devices.py
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

router = APIRouter()

# Check the flag: use Redis if the environment variable USE_REDIS is set to true.
USE_REDIS = os.getenv("USE_REDIS", "false").lower() in ("true", "1", "yes")

if USE_REDIS:
    import redis
    # Create a Redis client. decode_responses=True ensures we work with strings.
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    print("Using Redis for device state.")
else:
    # In-memory fallback for device states.
    device_states = {
        "lamp_status": "on",         # "on" or "off"
        "tv_status": "off",
        "radio_status": "off",
        "kitchenlight_status": "on",
        "tv_volume": "50",           # Volume percentage as string
        "radio_volume": "6",
    }
    print("Using in-memory device state storage.")

# Helper functions to get and set device status.
def get_device_status(key: str) -> str:
    if USE_REDIS:
        return r.get(key) or "off"
    else:
        return str(device_states.get(key, "off"))

def set_device_status(key: str, state: str):
    if USE_REDIS:
        r.set(key, state)
    else:
        device_states[key] = state

# Global variable for the Unity WebSocket connection.
unity_ws = None

class DeviceCommand(BaseModel):
    state: str  # Expected values: "on" or "off"

class VolumeCommand(BaseModel):
    change: float  # Percentage change (can be positive or negative)

# -----------------------------------------------------------
# WebSocket Endpoint
# -----------------------------------------------------------
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global unity_ws
    await websocket.accept()
    unity_ws = websocket
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from Unity: {data}")
            # Now we expect the message format: {device}:{property}:{value}
            parts = data.split(":")
            if len(parts) == 3:
                device = parts[0].lower()
                prop = parts[1].lower()  # e.g. "status", "volume", etc.
                value = parts[2].lower()
                key = f"{device}_{prop}"
                set_device_status(key, value)
    except WebSocketDisconnect:
        print("Unity disconnected")
        unity_ws = None

# -----------------------------------------------------------
# Device Endpoints (Lamp, TV, Radio, Kitchen Light)
# -----------------------------------------------------------

@router.post("/lamp")
async def toggle_lamp(command: DeviceCommand):
    global unity_ws
    if unity_ws is None:
        return {"error": "Unity client not connected"}
    desired_state = command.state.lower()
    current_state = get_device_status("lamp_status")
    if current_state == desired_state:
        return {"message": f"Lamp is already {desired_state}."}
    message = f"lamp:status:{command.state}"
    await unity_ws.send_text(message)
    set_device_status("lamp_status", desired_state)
    return {"message": "Command sent", "command": message}

@router.get("/lamp/status")
async def get_lamp_status():
    state = get_device_status("lamp_status")
    return {"lamp": state == "on"}

# -----------------------------------------------------------
# TV Endpoints
# -----------------------------------------------------------
@router.post("/tv")
async def toggle_tv(command: DeviceCommand):
    global unity_ws
    if unity_ws is None:
        return {"error": "Unity client not connected"}
    desired_state = command.state.lower()
    current_state = get_device_status("tv_status")
    if current_state == desired_state:
        return {"message": f"TV is already {desired_state}."}
    message = f"tv:status:{command.state}"
    await unity_ws.send_text(message)
    set_device_status("tv_status", desired_state)
    return {"message": "Command sent", "command": message}

@router.get("/tv/status")
async def get_tv_status():
    state = get_device_status("tv_status")
    return {"tv": state == "on"}

@router.post("/tv/volume")
async def change_tv_volume(command: VolumeCommand):
    global unity_ws
    if unity_ws is None:
        return {"error": "Unity client not connected"}
    message = f"tv:volume:{command.change}"
    await unity_ws.send_text(message)
    try:
        current_vol = int(get_device_status("tv_volume"))
    except:
        current_vol = 50
    new_vol = max(0, min(100, current_vol + int(command.change)))
    set_device_status("tv_volume", str(new_vol))
    return {"message": "TV volume command sent", "command": message, "new_volume": new_vol}

@router.get("/tv/volume")
async def get_tv_volume():
    vol = get_device_status("tv_volume")
    try:
        vol_int = int(vol)
    except:
        vol_int = 50
    return {"tv_volume": vol_int}

# -----------------------------------------------------------
# Radio Endpoints
# -----------------------------------------------------------
@router.post("/radio")
async def toggle_radio(command: DeviceCommand):
    global unity_ws
    if unity_ws is None:
        return {"error": "Unity client not connected"}
    desired_state = command.state.lower()
    current_state = get_device_status("radio_status")
    if current_state == desired_state:
        return {"message": f"Radio is already {desired_state}."}
    message = f"radio:status:{command.state}"
    await unity_ws.send_text(message)
    set_device_status("radio_status", desired_state)
    return {"message": "Command sent", "command": message}

@router.get("/radio/status")
async def get_radio_status():
    state = get_device_status("radio_status")
    return {"radio": state == "on"}

@router.post("/radio/volume")
async def change_radio_volume(command: VolumeCommand):
    global unity_ws
    if unity_ws is None:
        return {"error": "Unity client not connected"}
    message = f"radio:volume:{command.change}"
    await unity_ws.send_text(message)
    try:
        current_vol = int(get_device_status("radio_volume"))
    except:
        current_vol = 6
    new_vol = max(0, min(100, current_vol + int(command.change)))
    set_device_status("radio_volume", str(new_vol))
    return {"message": "Radio volume command sent", "command": message, "new_volume": new_vol}

@router.get("/radio/volume")
async def get_radio_volume():
    vol = get_device_status("radio_volume")
    try:
        vol_int = int(vol)
    except:
        vol_int = 6
    return {"radio_volume": vol_int}

# -----------------------------------------------------------
# Kitchen Wall Light Endpoints
# -----------------------------------------------------------
@router.post("/kitchenlight")
async def toggle_kitchen_light(command: DeviceCommand):
    global unity_ws
    if unity_ws is None:
        return {"error": "Unity client not connected"}
    desired_state = command.state.lower()
    current_state = get_device_status("kitchenlight_status")
    if current_state == desired_state:
        return {"message": f"Kitchen lights are already {desired_state}."}
    message = f"kitchenlight:status:{command.state}"
    await unity_ws.send_text(message)
    set_device_status("kitchenlight_status", desired_state)
    return {"message": "Command sent", "command": message}

@router.get("/kitchenlight/status")
async def get_kitchen_light_status():
    state = get_device_status("kitchenlight_status")
    return {"kitchenlight": state == "on"}
