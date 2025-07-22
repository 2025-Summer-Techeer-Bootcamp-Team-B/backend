from pydantic import BaseModel
from typing import Optional

class ImageProcessRequest(BaseModel):
    article_id: str

class ImageProcessResponse(BaseModel):
    message: str
    task_id: str
    status: str
    article_id: str 