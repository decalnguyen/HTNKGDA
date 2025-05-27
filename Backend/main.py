from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import cv2
import numpy as np
import asyncio

app = FastAPI()

latest_frame = None
frame_count = 0

@app.websocket("/ws/image")
async def websocket_endpoint(websocket: WebSocket):
    global latest_frame, frame_count
    await websocket.accept()
    print("🟢 WebSocket connected")

    try:
        while True:
            data = await websocket.receive_bytes()
            frame_count += 1
            print(f"📥 Frame {frame_count} received | Size: {len(data)} bytes")

            try:
                img = np.frombuffer(data, dtype=np.uint8).reshape((240, 240, 3))
            except Exception as e:
                print(f"❌ Không thể chuyển đổi frame {frame_count}: {e}")
                continue

            img = cv2.resize(img, (800, 400))

            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            lower = np.array([10, 100, 100])
            upper = np.array([25, 255, 255])
            mask = cv2.inRange(hsv, lower, upper)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            fire_detected = False
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 500:
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 255), 2)
                    fire_detected = True

            if fire_detected:
                cv2.putText(img, "🔥 FIRE DETECTED!", (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                cv2.putText(img, "No fire", (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            latest_frame = img

    except WebSocketDisconnect:
        print("🔴 WebSocket disconnected")

async def mjpeg_generator():
    global latest_frame
    while True:
        if latest_frame is not None:
            ret, jpeg = cv2.imencode(".jpg", latest_frame)
            if ret:
                frame = (b"--frame\r\n"
                         b"Content-Type: image/jpeg\r\n\r\n" +
                         jpeg.tobytes() + b"\r\n")
                yield frame
        else:
            blank = np.zeros((400, 800, 3), dtype=np.uint8)
            _, jpeg = cv2.imencode(".jpg", blank)
            frame = (b"--frame\r\n"
                     b"Content-Type: image/jpeg\r\n\r\n" +
                     jpeg.tobytes() + b"\r\n")
            yield frame
        await asyncio.sleep(0.05)

@app.get("/video")
async def video_stream():
    return StreamingResponse(mjpeg_generator(), media_type="multipart/x-mixed-replace; boundary=frame")
