import asyncio
import websockets
import cv2
import struct

async def send_frames(uri):
    async with websockets.connect(uri, ping_interval=None) as websocket:
        cap = cv2.VideoCapture('/dev/video9')  # Thay bằng index hoặc đường dẫn phù hợp

        if not cap.isOpened():
            print("[!] Không mở được camera.")
            return

        print("[✓] Kết nối thành công, bắt đầu gửi ảnh... (nhấn Ctrl+C để dừng)")

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("[!] Không thể đọc khung hình từ camera.")
                    break

                # Mã hóa frame thành JPEG
                success, encoded_image = cv2.imencode('.jpg', frame)
                if not success:
                    print("[!] Lỗi mã hóa JPEG.")
                    continue

                jpeg_data = encoded_image.tobytes()
                size_prefix = struct.pack(">I", len(jpeg_data))  # 4 byte header

                await websocket.send(size_prefix + jpeg_data)

                await asyncio.sleep(0.03)  # Gửi ~30 fps
        except KeyboardInterrupt:
            print("\n[✋] Đã dừng gửi ảnh.")
        finally:
            cap.release()

if __name__ == "__main__":
    uri = "ws://192.168.1.10:8000"  # Cập nhật đúng địa chỉ server
    asyncio.run(send_frames(uri))
