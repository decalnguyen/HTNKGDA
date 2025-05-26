from fastapi import FastAPI
from fastapi.responses import StreamingResponse, Response
import httpx
import cv2
import numpy as np
import time
import os
from datetime import datetime

app = FastAPI()

GATEWAY_STREAM_URL = "http://localhost:5000/video_feed"

# Tạo thư mục lưu ảnh nếu chưa có
SAVE_DIR = "fire_frames"
os.makedirs(SAVE_DIR, exist_ok=True)

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

                img = cv2.resize(img, (800, 400))

                # ==== AI phát hiện lửa bằng HSV ====
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                lower = np.array([10, 100, 100])
                upper = np.array([25, 255, 255])
                mask = cv2.inRange(hsv, lower, upper)

                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                fire_detected = False

                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if area > 5000:
                        x, y, w, h = cv2.boundingRect(cnt)
                        aspect_ratio = w / h if h != 0 else 0
                        if 0.8 < aspect_ratio < 2.0 and w > 50 and h > 50:
                            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
                            fire_detected = True

                # === Overlay văn bản & lưu ảnh nếu phát hiện ===
                if fire_detected:
                    cv2.putText(img, "🔥 FIRE DETECTED!", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # Lưu ảnh phát hiện
                    filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".jpg"
                    cv2.imwrite(os.path.join(SAVE_DIR, filename), img)
                else:
                    cv2.putText(img, "No fire", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                # Điều chỉnh tốc độ khung hình (~25 fps)
                time.sleep(1 / 60)

                # Encode và gửi ảnh về client
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
