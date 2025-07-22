from celery import Celery
import time
import asyncio
from app.services.article_service.image_process import process_image_to_s3
from app.services.tts_service.tts_generator import TTSGenerator
from app.core.database import get_db
from app.models.news_article import NewsArticle
from typing import Dict
from app.services.crawling_service.summarizer import summarize_article_with_gpt
from kombu import Queue

# Celery 앱 생성
celery_app = Celery(
    "worker",
    broker="amqp://guest:guest@rabbitmq:5672//",  # RabbitMQ 브로커
    backend="redis://redis:6379/0"                # Redis 결과 저장소
)

# 큐 설정 추가
celery_app.conf.task_default_queue = "default"
celery_app.conf.task_queues = (
    Queue("gpt"),
    Queue("tts"),
    Queue("image"),
    Queue("default"),
)

# 이미지 처리 태스크
@celery_app.task(queue='image')
def process_image_async(article_id: str):
    """비동기로 이미지를 처리하는 Celery 태스크"""
    try:
        # 새로운 데이터베이스 세션 생성 (Celery 워커에서 사용)
        db = next(get_db())
        result = process_image_to_s3(db, article_id)
        db.close()
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "article_id": article_id
        }

"""이미지 처리를 비동기로 시작하고 태스크 ID 반환"""
def process_image_to_s3_async_task(article_id: str):
    task = process_image_async.delay(article_id)
    return {
        "task_id": task.id,
        "status": "processing",
        "message": "이미지 처리가 시작되었습니다. 백그라운드에서 처리 중입니다."
    }


# TTS 생성 태스크
@celery_app.task(queue='tts')
def generate_tts_audio_async(article_id: str):
    """비동기로 TTS 오디오를 생성하는 Celery 태스크"""
    try:
        db = next(get_db())
        # 기사 정보 조회
        article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
        if not article:
            db.close()
            return {
                "success": False,
                "error": "기사를 찾을 수 없습니다.",
                "article_id": article_id
            }
        # 요약이 없으면 에러 반환
        if not article.summary_text:
            db.close()
            return {
                "success": False,
                "error": "요약이 없습니다. 먼저 요약을 생성하세요.",
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
            db.close()
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "article_id": article_id
        }

"""TTS 오디오 생성을 비동기로 시작하고 태스크 ID 반환"""
def generate_tts_audio_async_task(article_id: str)->Dict:
    task = generate_tts_audio_async.delay(article_id)
    return {
        "task_id": task.id,
        "status": "processing",
        "message": "TTS 오디오 생성이 시작되었습니다. 백그라운드에서 처리 중입니다."
    }

"""기사 요약 생성"""
@celery_app.task(queue='gpt')
def summarize_article_with_gpt_async(article_id: str):
    try:
        db = next(get_db())
        # article_id로 기사 조회
        article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
        if not article:
            db.close()
            return {
                "success": False,
                "error": "기사를 찾을 수 없습니다.",
                "article_id": article_id
            }
        # 요약 실행 (title, content 전달)
        summary = summarize_article_with_gpt(article.summary_text)
        # DB에 요약 저장
        article.summary_text = summary
        db.commit()
        db.refresh(article)
        db.close()
        # --- 요약 성공 후 TTS 태스크 호출 ---
        generate_tts_audio_async_task(article_id)
        # -----------------------------------
        return {
            "success": True,
            "article_id": article_id,
            "summary": summary
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "article_id": article_id
        }

def summarize_article_with_gpt_async_task(article_id: str):
    task = summarize_article_with_gpt_async.delay(article_id)
    return {
        "task_id": task.id,
        "status": "processing",
        "message": "기사 요약이 시작되었습니다. 백그라운드에서 처리 중입니다."
    }