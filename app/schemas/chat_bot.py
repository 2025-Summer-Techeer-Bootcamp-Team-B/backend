from pydantic import BaseModel
from typing import List, Optional

# Pydantic 모델들
class ChatMessage(BaseModel):
    message: str
    article_id: Optional[str] = None 
    conversation_id: Optional[str] = None 

class ChatResponse(BaseModel):
    conversation_id: str 
    response: str
    article_context: Optional[dict] = None 

class ArticleInfo(BaseModel):
    id: str
    title: str
    summary: str
    category: str
    press: str
    published_at: str
    url: str
    
class SearchResponse(BaseModel):
    articles: List[ArticleInfo]

class ConversationInfo(BaseModel):
    conversation_id: str
    message_count: int
    expires_in_seconds: int
    last_message: Optional[dict] = None

class ConversationDeleteResponse(BaseModel):
    message: str 