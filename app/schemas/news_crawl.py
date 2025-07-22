from pydantic import BaseModel
from typing import Optional, List

class NewsCrawledArticle(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    content: Optional[str] = None
    published_time: Optional[str] = None
    reporter_name: Optional[str] = None
    press_name: Optional[str] = None
    category: Optional[str] = None

    class Config:
        from_attributes = True

class NewsCrawlResponse(BaseModel):
    success: bool
    articles: List[NewsCrawledArticle]
    count: int
    processing_time: str
    save_to_db: bool
    timestamp: str 