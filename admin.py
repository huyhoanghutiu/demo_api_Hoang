from fastapi import APIRouter, HTTPException, Depends
from models import User
from sqlalchemy.orm import Session
from Function import get_db
from typing import List
from models import DBUser

router = APIRouter(prefix="/admin", tags=["ADMIN"])

@router.get("/users/", response_model=List[User])
def read_users(db: Session = Depends(get_db)):
    users = db.query(DBUser).all()
    return users

# Route để xóa người dùng từ cơ sở dữ liệu bằng ID
@router.delete("/user/{user_id}/", response_model=User)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return user

# Route để cập nhật thông tin người dùng bằng ID
@router.put("/user/{user_id}/", response_model=User)
def update_user(user_id: int, user: User, db: Session = Depends(get_db)):
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.username = user.username
    db.commit()
    return user