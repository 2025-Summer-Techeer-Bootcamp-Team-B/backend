from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(50), nullable=False)
    password = Column(String(100), nullable=False)
    voice_type = Column(String(50), nullable=True)
    refresh_token = Column(String(500), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, nullable=False, default=False)

    keywords = relationship("UserKeyword", back_populates="user")
    preferred_presses = relationship("UserPreferredPress", back_populates="user")
    article_histories = relationship("ArticleHistory", back_populates="user")
    user_categories = relationship("UserCategory", back_populates="user")

