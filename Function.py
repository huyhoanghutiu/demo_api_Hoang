
from sqlalchemy.orm import Session
from config import SessionLocal
from models import DBUser, User
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt



# Khởi tạo ngữ cảnh hash mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Xác thực OAuth2 Password Bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Phụ thuộc để lấy phiên làm việc với cơ sở dữ liệu
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Hàm để tạo người dùng mới
def create_user(db: Session, username: str, password: str, feature_vector = None, Images_profile = None):
    hashed_password = pwd_context.hash(password)
    db_user = DBUser(username=username, hashed_password=hashed_password, feature_vector=feature_vector, Images_profile = Images_profile)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Hàm để lấy người dùng từ cơ sở dữ liệu theo tên người dùng
def get_user(db: Session, username: str):
    return db.query(DBUser).filter(DBUser.username == username).first()

# Hàm để xác minh mật khẩu
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Hàm để tạo mã token với thời gian hết hạn
def create_access_token(data: dict):
    expires_delta = timedelta(hours=1)  # Đặt thời gian hết hạn của token là 1 giờ
    expire = datetime.utcnow() + expires_delta
    data.update({"exp": expire})
    return jwt.encode(data, "secret", algorithm="HS256")


class SimpleStorage:
    def __init__(self, base_dir="./images/"):
        self.base_dir = base_dir

    def save(self, file_id, file_content):
        """
        Lưu nội dung của file dưới dạng base64 vào thư mục đã chỉ định với ID của file được cung cấp.
        
        Parameters:
            file_id (str): ID của file.
            file_content (str): Nội dung của file dưới dạng base64.
        """
        with open(f"{self.base_dir}/{file_id}.txt", "w") as image_file:
            image_file.write(file_content)

    def read(self, file_id):
        """
        Đọc nội dung của file từ thư mục đã chỉ định dựa trên ID của file.
        
        Parameters:
            file_id (str): ID của file cần đọc.
        
        Returns:
            str: Nội dung của file dưới dạng base64.
            None: Nếu không tìm thấy file_id trong thư mục.
        """
        try:
            with open(f"{self.base_dir}/{file_id}.txt", "r") as image_file:
                return image_file.read()
        except FileNotFoundError:
            return None
        
#################################################

from redis import Redis

class RedisStorage:
    def __init__(self, redis_host, redis_port):
        self.redis = Redis(host=redis_host, port=redis_port)

    def save(self, file_id, file_content):
        self.redis.set(file_id, file_content)

    def read(self, file_id):
        return self.redis.get(file_id)
