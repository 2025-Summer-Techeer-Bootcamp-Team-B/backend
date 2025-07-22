from pydantic import BaseModel

class UserKeywordRequest(BaseModel):
    user_id: str  # UUID로 받는 경우 str로 처리

class ArticleResponse(BaseModel):
    id: str
    title: str
    content: str
    score: float