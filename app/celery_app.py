from celery import Celery
import time
import asyncio
from app.services.article_service.image_process import process_image_to_s3
from app.services.tts_service.tts_generator import TTSGenerator
from app.core.database import get_db
from app.models.news_article import NewsArticle
from typing import Dict

# Celery 앱 생성
celery_app = Celery(
    "worker",
    broker="amqp://guest:guest@rabbitmq:5672//",  # RabbitMQ 브로커
    backend="redis://redis:6379/0"                # Redis 결과 저장소
)

# 간단한 덧셈 태스크 정의
@celery_app.task
def add(x, y):
    time.sleep(5) # 테스트를 위해 5초 걸리는 작업 추가
    return x + y

# 이미지 처리 태스크
@celery_app.task
def process_image_async(article_id: str):
    """비동기로 이미지를 처리하는 Celery 태스크"""
    try:
        # 새로운 데이터베이스 세션 생성 (Celery 워커에서 사용)
        db = next(get_db())
        
        result = process_image_to_s3(db, article_id)
        
        # 세션 정리
        db.close()
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "article_id": article_id
        }

def process_image_to_s3_async(article_id: str) -> Dict:
    """이미지 처리를 비동기로 시작하고 태스크 ID 반환"""
    task = process_image_async.delay(article_id)
    
    return {
        "task_id": task.id,
        "status": "processing",
        "message": "이미지 처리가 시작되었습니다. 백그라운드에서 처리 중입니다."
    }

# TTS 생성 태스크
@celery_app.task
def generate_tts_audio_async(article_id: str):
    """비동기로 TTS 오디오를 생성하는 Celery 태스크"""
    try:
        # 새로운 데이터베이스 세션 생성
        db = next(get_db())
        
        # 기사 정보 조회
        article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
        if not article:
            return {
                "success": False,
                "error": "기사를 찾을 수 없습니다.",
                "article_id": article_id
            }
        
        # TTS 생성기 초기화
        tts_generator = TTSGenerator()
        
        # 비동기 함수를 동기적으로 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 남성/여성 음성 생성
            audio_urls = loop.run_until_complete(
                tts_generator.generate_male_female_audio(article.summary_text)
            )
            
            # 데이터베이스 업데이트
            article.male_audio_url = audio_urls["male_audio_url"]
            article.female_audio_url = audio_urls["female_audio_url"]
            db.commit()
            
            result = {
                "success": True,
                "article_id": article_id,
                "male_audio_url": audio_urls["male_audio_url"],
                "female_audio_url": audio_urls["female_audio_url"]
            }
            
        finally:
            loop.close()
        
        # 세션 정리
        db.close()
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "article_id": article_id
        }

def generate_tts_audio_async_task(article_id: str) -> Dict:
    """TTS 오디오 생성을 비동기로 시작하고 태스크 ID 반환"""
    task = generate_tts_audio_async.delay(article_id)
    
    return {
        "task_id": task.id,
        "status": "processing",
        "message": "TTS 오디오 생성이 시작되었습니다. 백그라운드에서 처리 중입니다."
    }