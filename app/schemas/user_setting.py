from pydantic import BaseModel
from typing import List, Optional

class UserSetting(BaseModel):
    press: Optional[List[str]] = None
    category: Optional[List[str]] = None
    keyword: Optional[List[str]] = None
    voice_type: Optional[str] = None

class UserHistoryItem(BaseModel):
    user_id: str
    news_id: str
    title: str
    thumbnail_image_url: str
    url: str
    category: str
    viewed_at: str

class UserHistory(BaseModel):
    histories: List[UserHistoryItem] 