from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.responses import Response
import httpx
import cv2
import numpy as np


app = FastAPI()

GATEWAY_STREAM_URL = "http://localhost:5000/video_feed"

def fire_detection_mjpeg():
    with httpx.stream("GET", GATEWAY_STREAM_URL, timeout=None) as response:
        print(f"Trying to stream from: {GATEWAY_STREAM_URL}")
        buffer = b""
        for chunk in response.iter_bytes():
            buffer += chunk
            start = buffer.find(b'\xff\xd8')
            end = buffer.find(b'\xff\xd9')
            if start != -1 and end != -1:
                jpg = buffer[start:end+2]
                buffer = buffer[end+2:]
                img = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
                
                # Resize ảnh về đúng kích thước mong muốn (theo pixel)
                img = cv2.resize(img, (800, 400))  # width x height
                # --- Giả lập phát hiện lửa: tô màu đỏ góc ảnh ---
                cv2.rectangle(img, (10, 10), (100, 100), (0, 0, 255), 2)
                cv2.putText(img, "TEST AI: FIRE?", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

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
