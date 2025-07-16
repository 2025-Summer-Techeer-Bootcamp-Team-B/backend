from fastapi import FastAPI, Depends, Request, Response
from .routers import example_router, user
from .core.database import engine, SessionLocal
from sqlalchemy.orm import Session
from app.core.database import Base
from app.models.user import User
from app.models.user_keyword import UserKeyword
from app.models.user_preferred_press import UserPreferredPress
from app.models.article_history import ArticleHistory
from app.models.press import Press
from app.models.news_article import NewsArticle
from fastapi.middleware.cors import CORSMiddleware
# from starlette.middleware.sessions import SessionMiddleware
from app.middleware.auth_middleware import AuthMiddleware
import os
from dotenv import load_dotenv

load_dotenv()


# 라우터 등록 (예시)
app.include_router(example_router.router)
app.include_router(async_crawl_router.router)

# Create tables
Base.metadata.create_all(bind=engine)
origins = [
    #추가해서 사용
]   

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SECRET_KEY = os.getenv("SECRET_KEY")
# app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# 인증 미들웨어 추가
app.add_middleware(AuthMiddleware)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/articles")
def read_articles(db: Session = Depends(get_db)):
    return db.query(NewsArticle).all()

@app.get("/test")
def create_Test_data():
    create_test_data()
    return {"message": "테스트 데이터 생성 완료"} 

# 라우터 등록
app.include_router(example_router.router)
app.include_router(user.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "News Briefing Backend is running."} 
