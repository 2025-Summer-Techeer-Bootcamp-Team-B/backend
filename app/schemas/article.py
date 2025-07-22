from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

class ArticleDetailResponse(BaseModel):
    id: UUID
    title: str
    url: str
    summary_text: Optional[str] = None
    female_audio_url: Optional[str]=None
    male_audio_url:Optional[str]=None
    original_iamge_url: Optional[str]=None
    thumbnail_image_url:Optional[str]=None
    category_name: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ArticleRecentResponse(BaseModel):
    id:UUID
    title:str
    thumbnail_image_url:Optional[str]=None
    category_name:Optional[str]=None
    author:Optional[str]=None
    published_at:Optional[datetime]=None

    class Config:
        from_attributes = True

class ArticleDeleteResponse(BaseModel):
    message: str
    article_id: str
