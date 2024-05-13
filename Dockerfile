# Sử dụng image base là Python 3
FROM python:3

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép tất cả các tệp và thư mục từ dự án của bạn vào container
COPY . /app

# Cài đặt các thư viện Python cần thiết, bao gồm uvicorn
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 6379 5432
EXPOSE 6379 5432 

# Khởi động ứng dụng khi container được chạy
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

