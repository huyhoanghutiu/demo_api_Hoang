
from fastapi import APIRouter, HTTPException, Depends, status,  UploadFile,File
from models import User
from sqlalchemy.orm import Session
from Function import get_db,get_user, oauth2_scheme, pwd_context, create_user, verify_password, create_access_token, SimpleStorage
from jose import jwt
from fastapi.security import OAuth2PasswordRequestForm
import base64
import uuid
from redis_utils import redis_client
import json
from typing import Optional
import time

router = APIRouter(tags=["USER"])

storage = SimpleStorage()

@router.post("/register/", response_model=User)
async def register_user(username: str, 
                        password: str, 
                        model_detect: Optional[str] = None,
                        model_extract: Optional[str] = None,
                        image: UploadFile = File(...), 
                        db: Session = Depends(get_db),
                        wait_time: int = 30):
    try:
        # Kiểm tra xem username đã được đăng ký chưa
        if get_user(db, username):
            raise HTTPException(status_code=400, detail="Username already registered")

        # Đọc dữ liệu từ tệp ảnh và mã hóa thành base64
        image_data = await image.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        data = {
            'image_base64': image_base64,
            'model_detect': model_detect,
            'model_extract': model_extract
        }

        # Tạo job_id để lưu trữ dữ liệu ảnh trong Redis
        job_id = f"register:{uuid.uuid4()}"

        # Lưu trữ dữ liệu ảnh base64 vào Redis với key là job_id
        redis_client.set(job_id, json.dumps(data))
        redis_client.lpush("Image_register", job_id)
        
        start_time = time.time()
        
        while time.time() - start_time <= wait_time:
            # Lấy kết quả xử lý ảnh từ Redis
            result_json = redis_client.get(f"result:{job_id}")
            if result_json:
                result_data = json.loads(result_json)
                # Lưu thông tin người dùng vào cơ sở dữ liệu
                new_user = create_user(db, username, password, feature_vector=result_data, Images_profile=job_id)
                # Nếu đăng ký thành công, lưu ảnh vào SimpleStorage
                storage.save(job_id, image_base64)
                return new_user  
            else:
                # Ngủ 1 giây trước khi kiểm tra lại
                time.sleep(1)

        # Nếu quá thời gian chờ mà vẫn chưa nhận được kết quả
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, 
                            detail=f"Không thể nhận được kết quả sau {wait_time} giây")

    except Exception as e:
        # Xảy ra lỗi trong quá trình xử lý
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# Route để đăng nhập và tạo mã token
@router.post("/token")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Route để lấy thông tin người dùng hiện tại
@router.get("/users/me/")
def read_users_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"username": username}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
@router.put("/users/update/")
def update_user_info(new_username: str, new_password: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Lấy thông tin người dùng từ cơ sở dữ liệu
        db_user = get_user(db, username)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Cập nhật thông tin người dùng
        if new_username:
            db_user.username = new_username
        if new_password:
            db_user.hashed_password = pwd_context.hash(new_password)
        
        db.commit()
        
        return {"message": "User information updated successfully"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    


from fastapi.responses import StreamingResponse
from io import BytesIO
from PIL import Image

storage = SimpleStorage(base_dir="./images/")  

@router.get("/image/{job_id}/")
async def get_image(job_id: str):
    # Lấy dữ liệu base64 từ SimpleStorage bằng job_id
    image_base64 = storage.read(job_id)
    if not image_base64:
        raise HTTPException(status_code=404, detail="Image not found")

    try:
        # Giải mã base64 thành dữ liệu ảnh
        image_data = base64.b64decode(image_base64)

        # Tạo một đối tượng PIL Image từ dữ liệu ảnh
        img = Image.open(BytesIO(image_data))

        # Tạo một buffer để lưu trữ ảnh
        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")  # Chọn định dạng ảnh (ví dụ: PNG)

        # Trả về phản hồi StreamingResponse cho người dùng
        img_buffer.seek(0)
        return StreamingResponse(img_buffer, media_type="image/png")  # Trả về dưới dạng PNG

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving image: {str(e)}")