from sqlalchemy import Column, Integer, String
from app.models.base import Base


class AdminUser(Base):
    """Admin user model for database-stored admin accounts.
    
    Note: The main superadmin is env-based and not stored in DB.
    """
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="admin", nullable=False)  # "admin", "viewer", etc.
