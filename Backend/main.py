from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import cv2
import numpy as np
import asyncio
import torch
import struct
import torchvision.transforms as T
from ultralytics import YOLO

app = FastAPI()

# === YOLOv8 Setup ===
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = YOLO("my_model.pt").to(device)
model.eval()

transform = T.Compose([
    T.ToPILImage(),
    T.Resize((320, 320)),
    T.ToTensor(),
])

# === Global Variables ===
latest_frame = None
frame_count = 0
esp32_websocket: WebSocket = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === ESP32 WebSocket Connection ===
@app.websocket("/ws/esp32")
async def esp32_ws(websocket: WebSocket):
    global esp32_websocket
    await websocket.accept()
    esp32_websocket = websocket
    print("🟢 ESP32 connected via WebSocket")

    try:
        while True:
            data = await websocket.receive_text()
            print("📩 ESP32 sent:", data)
    except WebSocketDisconnect:
        esp32_websocket = None
        print("🔴 ESP32 WebSocket disconnected")

# === WebSocket for Receiving Image Frames ===
@app.websocket("/ws/image")
async def websocket_image(websocket: WebSocket):
    global latest_frame, frame_count
    await websocket.accept()
    print("🟢 Image WebSocket connected")

    buffer = bytearray()
    expected_size = None

    try:
        while True:
            chunk = await websocket.receive_bytes()
            buffer.extend(chunk)

            while True:
                if expected_size is None and len(buffer) >= 4:
                    expected_size = struct.unpack(">I", buffer[:4])[0]
                    buffer = buffer[4:]
                elif expected_size is not None and len(buffer) >= expected_size:
                    frame_data = buffer[:expected_size]
                    buffer = buffer[expected_size:]
                    expected_size = None

                    # Decode and process frame
                    frame_count += 1
                    print(f"📥 Frame {frame_count} received | Size: {len(frame_data)} bytes")

                    np_arr = np.frombuffer(frame_data, np.uint8)
                    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    if img is None:
                        print(f"[!] Frame {frame_count} decode error")
                        continue

                    # Run fire detection
                    resized = cv2.resize(img, (320, 320))
                    rgb_img = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                    input_tensor = transform(rgb_img).unsqueeze(0).to(device)

                    with torch.no_grad():
                        result = model(input_tensor)[0]

                    # Draw boxes
                    annotated_img = img.copy()
                    if result.boxes is not None:
                        for box, cls in zip(result.boxes.xyxy, result.boxes.cls):
                            x1, y1, x2, y2 = map(int, box)
                            label = model.names[int(cls)]
                            color = (0, 0, 255) if label == "fire" else (0, 255, 0)
                            cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 2)
                            cv2.putText(annotated_img, label, (x1, max(0, y1 - 10)), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                    fire_detected = any(model.names[int(cls)] == "fire" for cls in result.boxes.cls)
                    status_text = "🔥 FIRE DETECTED" if fire_detected else "✅ No Fire"
                    status_color = (0, 0, 255) if fire_detected else (255, 255, 255)
                    cv2.putText(annotated_img, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)

                    latest_frame = annotated_img
                else:
                    break
    except WebSocketDisconnect:
        print("🔴 Image WebSocket disconnected")

# === Servo Control Endpoint ===
@app.post("/servo/control")
async def servo_control(request: Request):
    global esp32_websocket
    try:
        data = await request.json()
        code = int(data.get("code"))
        code = int(code)
        print(f"📥 Nhận mã điều khiển: {code}", type(code))
        if code not in [1, 2, 3, 4]:
            return JSONResponse(status_code=400, content={"message": "Invalid control code"})

        if esp32_websocket:
            await esp32_websocket.send_text(str(code))
            print(f"📨 Sent code {code} to ESP32")
            return {"status": "ok", "sent_code": code}
        else:
            print("⚠️ ESP32 not connected")
            return JSONResponse(status_code=503, content={"message": "ESP32 not connected"})
    except Exception as e:
        print(f"[!] Error in servo control: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})

# === MJPEG Streaming ===
async def mjpeg_generator():
    global latest_frame
    while True:
        frame = latest_frame if latest_frame is not None else np.zeros((320, 320, 3), dtype=np.uint8)
        ret, jpeg = cv2.imencode(".jpg", frame)
        if ret:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                jpeg.tobytes() + b"\r\n"
            )
        await asyncio.sleep(0.05)

@app.get("/video")
async def video_stream():
    return StreamingResponse(mjpeg_generator(), media_type="multipart/x-mixed-replace; boundary=frame")
