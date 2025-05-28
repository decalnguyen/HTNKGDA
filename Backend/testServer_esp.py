import asyncio
import websockets
import cv2
import numpy as np
import struct
import json

# Tập hợp các client kết nối
connected_clients = set()

async def handler(websocket):
    print(f"[+] New client connected: {websocket.remote_address}")
    connected_clients.add(websocket)

    buffer = bytearray()
    expected_size = None

    try:
        async for message in websocket:
            if isinstance(message, bytes):
                buffer.extend(message)

                while True:
                    # Chưa biết kích thước ảnh → cần ít nhất 4 byte đầu
                    if expected_size is None and len(buffer) >= 4:
                        expected_size = struct.unpack(">I", buffer[:4])[0]
                        buffer = buffer[4:]

                    # Nếu đã biết kích thước và đủ dữ liệu ảnh
                    if expected_size is not None and len(buffer) >= expected_size:
                        frame_data = buffer[:expected_size]
                        buffer = buffer[expected_size:]
                        expected_size = None

                        # Giải mã ảnh JPEG từ dữ liệu đã đủ
                        np_arr = np.frombuffer(frame_data, np.uint8)
                        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

                        if frame is not None:
                            cv2.imshow("ESP32-CAM Stream", frame)
                            if cv2.waitKey(1) & 0xFF == ord('q'):
                                break
                        else:
                            print("[!] Không giải mã được ảnh.")
                    else:
                        break
            else:
                print(f"[→] Text message received: {message}")
    except websockets.ConnectionClosed:
        print("[-] Client disconnected.")
    finally:
        connected_clients.remove(websocket)
        if not connected_clients:
            cv2.destroyAllWindows()

async def console_input_loop():
    """Task xử lý lệnh từ console và gửi JSON đến tất cả các client"""
    loop = asyncio.get_event_loop()
    while True:
        # Đọc lệnh từ stdin
        cmd = await loop.run_in_executor(None, input, "Enter servo value (0-10): ")
        cmd = cmd.strip()

        # Kiểm tra hợp lệ
        if not cmd.isdigit() or not (0 <= int(cmd) <= 10):
            print("[!] Giá trị phải là số nguyên từ 0 đến 10.")
            continue

        # Tạo JSON message
        msg = json.dumps({
            "cmd": 2,
            "servo": int(cmd)
        })

        # Gửi đến tất cả client đang kết nối
        if connected_clients:
            print(f"[→] Gửi lệnh đến {len(connected_clients)} client: {msg}")
            await asyncio.wait([ws.send(msg) for ws in connected_clients])
        else:
            print("[!] Chưa có client nào kết nối.")

async def main():
    # Khởi động WebSocket server
    server = await websockets.serve(handler, "0.0.0.0", 8080, ping_interval=None)
    print("[✓] Server đang chạy tại ws://0.0.0.0:8080")

    # Tạo task đọc lệnh từ console
    asyncio.create_task(console_input_loop())

    # Giữ server chạy mãi
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Server dừng bởi người dùng.")