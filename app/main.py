from fastapi import FastAPI, Depends
from app.middleware.auth_middleware import AuthMiddleware
from app.routers import router
from app.utils.scheduler import start_scheduler
from .core.database import engine, SessionLocal
from sqlalchemy.orm import Session
from app.core.database import Base
from app.models.news_article import NewsArticle
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv
from prometheus_fastapi_instrumentator import Instrumentator

load_dotenv()

app=FastAPI()  

instrumentator = Instrumentator().instrument(app)
instrumentator.expose(app, include_in_schema=False) # 메트릭 정보 확인

app.include_router(router)
# Create tables
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

#인증 미들웨어 추가
app.add_middleware(AuthMiddleware)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "News Briefing Backend is running."} 

@app.get("/articles")
def read_articles(db: Session = Depends(get_db)):
    return db.query(NewsArticle).all()


# 서버 시작 시 전체 기사 크롤링 한번 실행
# 이후 매 15분마다 자동 크롤링
@app.on_event("startup")
def startup_event():
    start_scheduler(app)
    # 서버 시작 시 즉시 한 번 실행은 제거됨
    # import asyncio
    # loop = asyncio.get_event_loop()
    # loop.create_task(scrape_all_articles_async(max_concurrent=10, save_to_db=True))