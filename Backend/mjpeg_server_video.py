from flask import Flask, Response
import cv2

app = Flask(__name__)

# Đường dẫn đến file video
VIDEO_PATH = "video.mp4"  # ← thay bằng tên file video của bạn

def generate_frames():
    cap = cv2.VideoCapture(VIDEO_PATH)
    while True:
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # tua lại từ đầu khi hết video
            continue

        # Encode ảnh thành JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Trả về frame theo chuẩn MJPEG
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
