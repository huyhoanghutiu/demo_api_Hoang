from fastapi import APIRouter, HTTPException, Depends, status, UploadFile,File
from Function import  oauth2_scheme
import base64
from jose import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import json
from redis_utils import redis_client
import uuid
from typing import Optional
import time


router = APIRouter(prefix="/images", tags=["IDENTIFY"])

@router.post("/upload-image-identify/")
async def upload_image_identify(
    model_identify: Optional[str] = None,
    model_extract: Optional[str] = None,
    token: str = Depends(oauth2_scheme),
    file: UploadFile = File(...),
    wait_time: int = 30,  # Thời gian chờ giây (mặc định là 30 giây)
):
    try:
        # Giải mã token để lấy thông tin người dùng từ trường 'sub'
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
        username = payload.get("sub")
        
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token không hợp lệ",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generate a unique ID for the image
        job_id = f"identify:{str(uuid.uuid4())}"
        
        # Đọc và mã hóa dữ liệu hình ảnh thành base64
        image_data = await file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Chuẩn bị dữ liệu JSON để lưu vào Redis
        data = {
            'image_base64': image_base64,
            'model_identify': model_identify,
            'model_extract': model_extract
        }
        
        # Chuyển đổi dictionary thành chuỗi JSON
        json_data = json.dumps(data)
        
        # Lưu dữ liệu JSON vào Redis với key là job_id
        redis_client.set(job_id, json_data)
        redis_client.lpush("job_queue", job_id)

        start_time = time.time()
        while True:
            result_json = redis_client.get(f"result:{job_id}")
            if result_json:
                result_data = json.loads(result_json)
                break
            if time.time() - start_time > wait_time:
                # Nếu quá thời gian chờ, trả về lỗi thời gian chờ hết
                raise HTTPException(
                    status_code=status.HTTP_408_REQUEST_TIMEOUT,
                    detail=f"Không thể nhận được kết quả sau {wait_time} giây",
                )
            # Ngủ 1 giây trước khi kiểm tra lại
            time.sleep(1)

        # Trả về phản hồi thành công với kết quả
        return result_data

    except (ExpiredSignatureError, InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token hết hạn hoặc không hợp lệ",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Máy chủ không phản hồi : " + str(e),
        )
    
