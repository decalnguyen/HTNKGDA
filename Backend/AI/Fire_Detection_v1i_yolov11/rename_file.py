import os
import re

folder_path = r'data\labels'

print("Current working directory:", os.getcwd())

if not os.path.exists(folder_path):
    print(f"❌ Thư mục không tồn tại: {folder_path}")
    exit()

for filename in os.listdir(folder_path):
    first_char = filename[0]

    # Tìm dãy số sau dấu '-' đầu tiên
    match = re.search(r'-([0-9]+)', filename)
    number_part = match.group(1) if match else "noNumber"

    # Tách phần tên và phần mở rộng
    base, ext = os.path.splitext(filename)

    # Tạo tên mới giữ phần mở rộng
    new_name = f"{first_char}_{number_part}{ext}"

    old_path = os.path.join(folder_path, filename)
    new_path = os.path.join(folder_path, new_name)

    os.rename(old_path, new_path)
    print(f'✅ Đổi tên: {filename} -> {new_name}')
