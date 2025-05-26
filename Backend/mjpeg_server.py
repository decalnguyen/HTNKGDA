from flask import Flask, Response
import cv2

app = Flask(__name__)

# Bạn có thể đổi thành đường dẫn file video như 'test.mp4' nếu không dùng webcam
video_source = 0  # 0 là webcam mặc định

def generate_frames():
    cap = cv2.VideoCapture(video_source)
    while True:
        success, frame = cap.read()
        if not success:
            break
        # Chuyển frame sang JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        # Trả về từng frame theo chuẩn MJPEG
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
