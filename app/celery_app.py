from celery import Celery
from kombu import Queue
import asyncio
from typing import Dict
from app.services.thumbnails.thumbnail_service import process_image_to_gcs
from app.core.database import get_db
from app.models.news_article import NewsArticle
from app.services.tts.tts_service import TTSService

# Celery 앱 생성
celery_app = Celery(
    "worker",
    broker="amqp://guest:guest@rabbitmq:5672//",  # RabbitMQ 브로커
    backend="redis://redis:6379/0"                # Redis 결과 저장소
)

# 큐 설정 추가
celery_app.conf.task_default_queue = "default"
celery_app.conf.task_queues = (
    Queue("tts"),
    Queue("image"),
    Queue("default"),
)

def process_image_to_gcs_async_task(article_id: str) -> Dict:
    """이미지 처리 Celery 태스크를 비동기로 시작하고 태스크 ID 반환"""
    task = process_image_async.delay(article_id)
    return {
        "task_id": task.id,
        "status": "processing",
        "message": "이미지 처리가 시작되었습니다. 백그라운드에서 처리 중입니다."
    }

@celery_app.task(queue='image')
def process_image_async(article_id: str) -> Dict:
    """
    비동기로 이미지를 처리하는 Celery 태스크
    """
    try:
        result = process_image_to_gcs(article_id)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "article_id": article_id
        }

def generate_tts_audio_async_task(article_id: str) -> Dict:
    """TTS 오디오 생성 Celery 태스크를 비동기로 시작하고 태스크 ID 반환"""
    task = generate_tts_audio_async.delay(article_id)
    return {
        "task_id": task.id,
        "status": "processing",
        "message": "TTS 오디오 생성이 시작되었습니다. 백그라운드에서 처리 중입니다."
    }

@celery_app.task(queue='tts')
def generate_tts_audio_async(article_id: str) -> Dict:
    """
    비동기로 TTS 오디오를 생성하는 Celery 태스크
    """
    db = next(get_db())
    try:
        article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
        if not article:
            return {
                "success": False,
                "error": "기사를 찾을 수 없습니다.",
                "article_id": article_id
            }
        if not article.summary_text:
            return {
                "success": False,
                "error": "요약이 없습니다. 먼저 요약을 생성하세요.",
                "article_id": article_id
            }
        
        print(f"TTS 생성 시작: article_id={article_id}, summary_length={len(article.summary_text)}")
        
        tts_service = TTSService()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            audio_urls = loop.run_until_complete(
                tts_service.generate_male_female_audio(article.summary_text)
            )
            
            print(f"TTS 생성 결과: {audio_urls}")
            
            if not audio_urls.get("male_audio_url") or not audio_urls.get("female_audio_url"):
                error_msg = f"TTS 생성 실패 - male_url: {audio_urls.get('male_audio_url')}, female_url: {audio_urls.get('female_audio_url')}"
                print(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "article_id": article_id
                }
            
            article.male_audio_url = audio_urls["male_audio_url"]
            article.female_audio_url = audio_urls["female_audio_url"]
            db.commit()
            
            print(f"TTS 생성 성공: male_url={audio_urls['male_audio_url']}, female_url={audio_urls['female_audio_url']}")
            
            return {
                "success": True,
                "article_id": article_id,
                "male_audio_url": audio_urls["male_audio_url"],
                "female_audio_url": audio_urls["female_audio_url"]
            }
        finally:
            loop.close()
    except Exception as e:
        db.rollback()
        error_msg = f"TTS 생성 중 예외 발생: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "article_id": article_id
        }
    finally:
        db.close()