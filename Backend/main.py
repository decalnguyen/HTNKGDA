from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import cv2
import numpy as np
import asyncio
import torch
import torchvision.transforms as T
from ultralytics import YOLO

app = FastAPI()

# === 🧠 Load mô hình YOLO đã huấn luyện ===
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = YOLO("my_model.pt").to(device)
model.eval()

FIRE_CLASSES = ['fire']  # Đảm bảo tên lớp trùng với model.names

# Chuẩn hóa ảnh đầu vào
transform = T.Compose([
    T.ToPILImage(),
    T.Resize((320, 320)),
    T.ToTensor(),
])

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

            # Resize ảnh cho model
            img_for_model = cv2.resize(img, (320, 320))
            input_tensor = transform(img_for_model).unsqueeze(0).to(device)

            # Ảnh để hiển thị (scale lớn)
            display_img = cv2.resize(img, (320, 320))

            # Tính tỉ lệ scale để vẽ bounding box
            scale_x = display_img.shape[1] / 320
            scale_y = display_img.shape[0] / 320

            with torch.no_grad():
                results = model(input_tensor)[0]
                boxes = results.boxes

            fire_detected = False

            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                label = model.names[cls_id]

                if label in FIRE_CLASSES:
                    # Scale lại vị trí khung để vẽ trên ảnh lớn
                    x1 = int(x1 * scale_x)
                    y1 = int(y1 * scale_y)
                    x2 = int(x2 * scale_x)
                    y2 = int(y2 * scale_y)

                    cv2.rectangle(display_img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(display_img, f"{label} {conf:.2f}", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    fire_detected = True

            if fire_detected:
                cv2.putText(display_img, "🔥 FIRE DETECTED (YOLOv11)", (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                cv2.putText(display_img, "No fire", (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            latest_frame = display_img

    except WebSocketDisconnect:
        print("🔴 WebSocket disconnected")


async def mjpeg_generator():
    global latest_frame
    while True:
        if latest_frame is not None:
            ret, jpeg = cv2.imencode(".jpg", latest_frame)
            if ret:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" +
                       jpeg.tobytes() + b"\r\n")
        else:
            blank = np.zeros((320, 320, 3), dtype=np.uint8)
            _, jpeg = cv2.imencode(".jpg", blank)
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" +
                   jpeg.tobytes() + b"\r\n")
        await asyncio.sleep(0.05)


@app.get("/video")
async def video_stream():
    return StreamingResponse(mjpeg_generator(), media_type="multipart/x-mixed-replace; boundary=frame")
