from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class ArticleRecommendResponse(BaseModel):
    id:str
    title:str
    content:str
    thumbnail_image_url:Optional[str]=None
    category_name:Optional[str]=None
    author:Optional[str]=None
    published_at:Optional[datetime]=None
    score:Optional[float]=None

    class Config:
        from_attributes = True