from redis import Redis
import os

# Lấy giá trị của biến môi trường REDIS_HOST, nếu không có thì mặc định là localhost
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = 6379

# Khởi tạo đối tượng Redis để gửi tin nhắn tới Redis channel
redis_client = Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)