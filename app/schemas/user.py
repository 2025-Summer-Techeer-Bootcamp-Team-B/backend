from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: str
    password: str

class RegisterResponse(BaseModel):
    message: str
    email: str
    access_token: str
    refresh_token: str

class LoginResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str

class RefreshRequest(BaseModel):
    refresh_token: str

class UserHistory(BaseModel):
    user_id: str
    news_id: str
    title: str
    thumbnail_image_url: str
    url: str
    category: str
    viewed_at: datetime

class EmailExistsResponse(BaseModel):
    exists: bool
    email: str