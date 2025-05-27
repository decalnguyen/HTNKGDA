import cv2
import websockets
import asyncio
import numpy as np

WEBSOCKET_URL = "ws://localhost:8000/ws/image"
VIDEO_PATH = "video.mp4"  # hoặc 0 nếu dùng webcam

async def send_raw_frames():
    try:
        async with websockets.connect(WEBSOCKET_URL, max_size=None) as websocket:
            print("🟢 Đã kết nối WebSocket tới server")

            cap = cv2.VideoCapture(VIDEO_PATH)
            frame_id = 0

            while True:
                success, frame = cap.read()
                if not success:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue

                frame = cv2.resize(frame, (240, 240))
                raw_data = frame.tobytes()

                await websocket.send(raw_data)

                print(f"📤 Frame {frame_id} sent | Size: {len(raw_data)} bytes")
                frame_id += 1

                await asyncio.sleep(1 / 20)

    except Exception as e:
        print(f"❌ Lỗi kết nối WebSocket: {e}")

if __name__ == "__main__":
    asyncio.run(send_raw_frames())
