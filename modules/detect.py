# import cv2
# import numpy as np
# import base64

# def process_detect_job(redis_conn, job_key, image_base64):
#     try:
#         # Giải mã dữ liệu hình ảnh từ base64
#         image_data = base64.b64decode(image_base64)
#         np_arr = np.frombuffer(image_data, np.uint8)
#         decoded_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

#         # Xử lý detect ở đây - ví dụ, phát hiện khuôn mặt
#         face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
#         gray_image = cv2.cvtColor(decoded_image, cv2.COLOR_BGR2GRAY)
#         faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

#         # Vẽ khung xung quanh các khuôn mặt được phát hiện
#         for (x, y, w, h) in faces:
#             cv2.rectangle(decoded_image, (x, y), (x + w, y + h), (255, 0, 0), 2)

#         # Chuyển đổi ảnh kết quả về base64
#         _, encoded_result = cv2.imencode('.jpg', decoded_image)
#         result_base64 = base64.b64encode(encoded_result).decode('utf-8')

#         # Lưu kết quả vào Redis
#         redis_conn.set(f"{job_key}", result_base64)

#         print(f"Xử lý detect thành công cho {job_key}")
#     except Exception as ex:
#         print(f"Lỗi xử lý detect cho {job_key}: {str(ex)}")

