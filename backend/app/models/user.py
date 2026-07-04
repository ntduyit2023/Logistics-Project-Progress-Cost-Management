from datetime import datetime
from typing import List
from sqlalchemy import String, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.database import Base


class User(Base):
    """
    Quản lý thông tin người dùng trong hệ thống GLPO.

    Attributes:
        id (int): Khóa chính.
        username (str): Tên đăng nhập duy nhất.
        email (str): Địa chỉ email duy nhất.
        created_at (datetime): Thời điểm tạo tài khoản.
        projects (List[AppProject]): Danh sách dự án thuộc sở hữu (Quan hệ 1-N).
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    projects: Mapped[List["AppProject"]] = relationship(back_populates="owner")
