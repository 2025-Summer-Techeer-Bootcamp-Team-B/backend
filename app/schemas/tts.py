from pydantic import BaseModel
from typing import Optional

class TTSRequest(BaseModel):
    article_id: str
    voice_type: Optional[str] = "female"  # 기본값 female

class TTSResponse(BaseModel):
    message: str
    task_id: str
    status: str

class TTSStatusResponse(BaseModel):
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    task_id: Optional[str] = None

class ArticleAudioResponse(BaseModel):
    article_id: str
    title: str
    male_audio_url: Optional[str] = None
    female_audio_url: Optional[str] = None
    has_audio: bool 