from ultralytics import YOLO

# Load model đã huấn luyện
model = YOLO(r'my_model.pt')  # <-- Đường dẫn đến model của bạn

# Chạy test trên thư mục chứa ảnh
results = model.predict(source=r"AI\fire-dataset\data\validation\images",  # Thư mục chứa ảnh test
                        save=True,        # Lưu ảnh đầu ra (có vẽ box)
                        save_txt=True,    # Lưu file txt chứa prediction
                        conf=0.25,        # Ngưỡng confidence
                        iou=0.45,         # Ngưỡng IOU khi NMS
                        imgsz=640,        # Kích thước resize ảnh
                        show=False)       # Hiển thị ảnh (có thể dùng True nếu chạy local)

# In kết quả dự đoán đầu tiên
print(results[0].names)     # Tên các class
print(results[0].boxes)     # Tọa độ bounding boxes