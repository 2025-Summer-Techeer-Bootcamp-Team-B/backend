from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import uuid

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    url = Column(String(225), nullable=False)
    published_at = Column(DateTime, nullable=False)
    summary_text = Column(String, nullable=False)
    male_audio_url = Column(String(100), nullable=False)
    female_audio_url = Column(String(100), nullable=False)
    original_image_url = Column(String(200))
    thumbnail_image_url = Column(String(200))
    author = Column(String(20), nullable=False)
    category_name = Column(String(30), nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, nullable=False, default=False)

    press_id = Column(UUID(as_uuid=True), ForeignKey("presses.id"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    
    press = relationship("Press", back_populates="articles")
    category = relationship("Category", back_populates="news_articles")

    histories = relationship("ArticleHistory", back_populates="article")
