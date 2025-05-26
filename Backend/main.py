from fastapi import FastAPI
from fastapi.responses import StreamingResponse, Response
import httpx
import cv2
import numpy as np
import torch

app = FastAPI()

GATEWAY_STREAM_URL = "http://localhost:5000/video_feed"

# 🧠 Load YOLOv5 model — thay 'best.pt' bằng model của bạn
# Lần đầu chạy sẽ tự tải yolov5 repo về
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')  # model mặc định
model.conf = 0.5  # confidence threshold
model.iou = 0.45  # NMS IoU threshold

# Nếu bạn biết class id cho "fire", ví dụ trong dataset bạn dùng id = 0
FIRE_CLASS_ID = 0

def fire_detection_mjpeg():
    with httpx.stream("GET", GATEWAY_STREAM_URL, timeout=None) as response:
        print(f"🔄 Streaming from: {GATEWAY_STREAM_URL}")
        buffer = b""
        for chunk in response.iter_bytes():
            buffer += chunk
            start = buffer.find(b'\xff\xd8')
            end = buffer.find(b'\xff\xd9')
            if start != -1 and end != -1:
                jpg = buffer[start:end+2]
                buffer = buffer[end+2:]
                img = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
                if img is None:
                    continue

                # Resize để dễ xử lý
                img = cv2.resize(img, (800, 400))

                # ==== 🚀 AI phát hiện bằng YOLOv5 ====
                results = model(img)
                fire_detected = False

                # Lấy kết quả bbox: [x1, y1, x2, y2, conf, class]
                for *xyxy, conf, cls in results.xyxy[0]:
                    class_id = int(cls)
                    if class_id == FIRE_CLASS_ID:
                        x1, y1, x2, y2 = map(int, xyxy)
                        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(img, f"FIRE {conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        fire_detected = True

                # Ghi chú lên ảnh
                if fire_detected:
                    cv2.putText(img, "🔥 FIRE DETECTED (YOLOv5)", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                else:
                    cv2.putText(img, "No fire", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                # Encode lại ảnh và stream
                ret, jpeg = cv2.imencode(".jpg", img)
                if not ret:
                    continue
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n"
                )

@app.get("/video")
def stream_video():
    try:
        return StreamingResponse(fire_detection_mjpeg(), media_type="multipart/x-mixed-replace; boundary=frame")
    except Exception as e:
        print("⚠️ Lỗi khi kết nối stream:", e)
        return Response("Không thể kết nối tới nguồn MJPEG", status_code=500)
