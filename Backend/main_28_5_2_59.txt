from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import cv2
import numpy as np
import asyncio
import torch
import torchvision.transforms as T
from ultralytics import YOLO

app = FastAPI()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = YOLO("my_model.pt").to(device)
model.eval()

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
                print(f" Không thể chuyển đổi frame {frame_count}: {e}")
                continue

            # Resize ảnh và chuẩn hóa để đưa vào model
            img_for_model = cv2.resize(img, (320, 320))
            img_for_model = cv2.cvtColor(img_for_model, cv2.COLOR_BGR2RGB)  # <- thêm dòng này
            input_tensor = transform(img_for_model).unsqueeze(0).to(device)

            # ===  Dự đoán ===
            with torch.no_grad():
                results = model(input_tensor)[0]

            # ===  Lấy ảnh có vẽ bounding box từ kết quả ===
            # annotated_img = results.plot()[0]  # Đây là ảnh có bbox đã vẽ sẵn

            # ✅ Thay bằng:
            annotated_img = img.copy()
            boxes = results.boxes
            if boxes is not None and len(boxes) > 0:
                for box, cls in zip(boxes.xyxy, boxes.cls):
                    x1, y1, x2, y2 = map(int, box[:4])
                    label = model.names[int(cls)]
                    cv2.rectangle(annotated_img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(annotated_img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)           

            # Ghi trạng thái đơn giản
            fire_detected = any(model.names[int(cls)] == "fire" for cls in results.boxes.cls)
            status_text = " FIRE DETECTED" if fire_detected else "No fire"
            status_color = (0, 255, 0) if fire_detected else (255, 255, 255)
            cv2.putText(annotated_img, status_text, (10, 310),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)

            latest_frame = annotated_img

    except WebSocketDisconnect:
        print(" WebSocket disconnected")


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
