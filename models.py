from pydantic import BaseModel
from config import Base, engine
from sqlalchemy import Column, Integer, String, Sequence, PickleType
from sqlalchemy.orm import relationship
from typing import List

# Pydantic model cho User
class User(BaseModel):
    id: int
    username: str
    feature_vector: List[float]
    Images_profile: str

# SQLAlchemy model cho User
class DBUser(Base):
    __tablename__ = "users"

    id = Column(Integer, Sequence('user_id_seq'), primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    feature_vector =Column(PickleType)
    Images_profile = Column(String)

# Tạo bảng cơ sở dữ liệu nếu chưa tồn tại
Base.metadata.create_all(bind=engine)