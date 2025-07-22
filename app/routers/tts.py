from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.news_article import NewsArticle
from app.celery_app import generate_tts_audio_async_task
from celery.result import AsyncResult
from typing import Dict

router = APIRouter(prefix="/tts", tags=["TTS"])

@router.post("/generate/{article_id}")
async def generate_tts_for_article(article_id: str, db: Session = Depends(get_db)):
    """
    특정 기사에 대한 TTS 오디오 생성 요청
    """
    # 기사 존재 확인
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다.")
    
    # TTS 태스크 시작
    task_result = generate_tts_audio_async_task(article_id)
    
    return {
        "message": "TTS 오디오 생성이 시작되었습니다.",
        "task_id": task_result["task_id"],
        "status": task_result["status"]
    }

@router.get("/status/{task_id}")
async def get_tts_status(task_id: str):
    """
    TTS 생성 태스크 상태 확인
    """
    task_result = AsyncResult(task_id)
    
    if task_result.ready():
        if task_result.successful():
            result = task_result.result
            return {
                "status": "completed",
                "result": result
            }
        else:
            return {
                "status": "failed",
                "error": str(task_result.result)
            }
    else:
        return {
            "status": "processing",
            "task_id": task_id
        }

@router.get("/article/{article_id}/audio")
async def get_article_audio(article_id: str, db: Session = Depends(get_db)):
    """
    기사의 오디오 URL 조회
    """
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다.")
    
    return {
        "article_id": str(article.id),
        "title": article.title,
        "male_audio_url": article.male_audio_url,
        "female_audio_url": article.female_audio_url,
        "has_audio": bool(article.male_audio_url and article.female_audio_url)
    } 