from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import cv2
import numpy as np
import asyncio
import torch
import struct
import torchvision.transforms as T
from ultralytics import YOLO
from fastapi.responses import JSONResponse


app = FastAPI()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = YOLO("my_model.pt").to(device)
model.eval()
fire_status = "No Fire"
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

    buffer = bytearray()
    expected_size = None

    try:
        while True:
            try:
                message = await websocket.receive_bytes()
            except Exception as e:
                print(f"[!] Lỗi nhận message: {e}")
                break

            buffer.extend(message)

            while True:
                # Nếu chưa xác định được expected_size mà buffer đủ 4 byte
                if expected_size is None:
                    if len(buffer) >= 4:
                        expected_size = struct.unpack(">I", buffer[:4])[0]
                        buffer = buffer[4:]
                    else:
                        break  # Chưa đủ 4 byte, đợi thêm

                # Khi đã có expected_size, đợi đủ dữ liệu
                if expected_size is not None:
                    if len(buffer) >= expected_size:
                        frame_data = buffer[:expected_size]
                        buffer = buffer[expected_size:]
                        expected_size = None

                        frame_count += 1
                        print(f"📥 Frame {frame_count} received | Size: {len(frame_data)} bytes")

                        # Decode JPEG
                        np_arr = np.frombuffer(frame_data, np.uint8)
                        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

                        if img is None:
                            print(f"[!] Frame {frame_count} không thể decode JPEG.")
                            continue

                        # Resize ảnh và chuẩn hóa để đưa vào model
                        img_for_model = cv2.resize(img, (320, 320))
                        img_for_model = cv2.cvtColor(img_for_model, cv2.COLOR_BGR2RGB)
                        input_tensor = transform(img_for_model).unsqueeze(0).to(device)

                        # ===  Dự đoán ===
                        with torch.no_grad():
                            results = model(input_tensor)[0]

                        # ===  Vẽ bounding box lên ảnh ===
                        annotated_img = img.copy()
                        boxes = results.boxes
                        if boxes is not None and len(boxes) > 0:
                            h_orig, w_orig = img.shape[:2]
                            scale_x = w_orig / 320
                            scale_y = h_orig / 320

                            for box, cls in zip(boxes.xyxy, boxes.cls):
                                x1, y1, x2, y2 = box[:4]
                                # Scale back to original image size
                                x1 = int(x1 * scale_x)
                                y1 = int(y1 * scale_y)
                                x2 = int(x2 * scale_x)
                                y2 = int(y2 * scale_y)

                                label = model.names[int(cls)]
                                cv2.rectangle(annotated_img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                                cv2.putText(annotated_img, label, (x1, max(0, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                        # Ghi trạng thái đơn giản
                        fire_detected = any(model.names[int(cls)] == "fire" for cls in results.boxes.cls)

                        # Annotate ảnh
                        status_text = "FIRE DETECTED" if fire_detected else "NO FIRE"
                        status_color = (0, 0, 255) if fire_detected else (255, 255, 255)

                        cv2.putText(annotated_img, status_text, (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)

                        latest_frame = annotated_img
                    else:
                        break  # Chưa đủ dữ liệu, đợi thêm
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
