import datetime
import uuid
import logging
import hashlib
import os
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from dateutil import parser
from app.models.news_article import NewsArticle
from app.models.press import Press
from app.models.category import Category
from app.celery_app import process_image_to_s3_async_task, generate_tts_audio_async_task

logger = logging.getLogger(__name__)
KST = datetime.timezone(datetime.timedelta(hours=9))


def parse_published_time(time_str: Optional[str]) -> datetime.datetime:
    """
    발행 시간 문자열을 datetime 객체(KST)로 파싱합니다.
    Args:
        time_str (Optional[str]): 발행 시간 문자열
    Returns:
        datetime.datetime: KST 타임존이 적용된 datetime 객체
    """
    if not time_str:
        return datetime.datetime.now(KST)
    try:
        dt = parser.parse(time_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(KST)
    except Exception as e:
        logger.warning(f"시간 파싱 실패: {time_str} ({e})")
        return datetime.datetime.now(KST)


def get_or_create_press(db: Session, press_name: str) -> Press:
    press = db.query(Press).filter(
        Press.press_name == press_name,
        Press.is_deleted == False
    ).first()
    if not press:
        press = Press(press_name=press_name)
        db.add(press)
        db.commit()
        db.refresh(press)
        logger.info(f"새 언론사 생성: {press.press_name}")
    return press


def get_or_create_category(db: Session, category_name: str) -> Category:
    category = db.query(Category).filter(
        Category.category_name == category_name,
        Category.is_deleted == False
    ).first()
    if not category:
        category = Category(category_name=category_name)
        db.add(category)
        db.commit()
        db.refresh(category)
        logger.info(f"새 카테고리 생성: {category.category_name}")
    return category


def save_article_to_db(db: Session, article_data: Dict) -> Optional[NewsArticle]:
    """
    기사 데이터를 DB에 저장하고, 후처리 태스크(TTS, 이미지)를 비동기로 실행
    """
    try:
        # 필수 필드 검증
        if not article_data.get('title') or not article_data.get('url'):
            logger.warning(f"필수 필드 누락: title={article_data.get('title')}, url={article_data.get('url')}")
            return None
        # URL 중복 체크
        existing_article = db.query(NewsArticle).filter(
            NewsArticle.url == article_data['url'],
            NewsArticle.is_deleted == False
        ).first()
        if existing_article:
            logger.info(f"이미 존재하는 기사: {article_data['url']}")
            return existing_article
        # 언론사/카테고리
        press = get_or_create_press(db, article_data.get('press_name', 'unknown'))
        category = get_or_create_category(db, article_data.get('category', 'general'))
        # 발행 시간
        published_at = parse_published_time(article_data.get('published_time'))
        if not published_at:
            published_at = datetime.datetime.now(KST)
        article_id = str(uuid.uuid4())
        # 기자명 처리
        reporter_name = article_data.get('reporter_name')
        author = reporter_name[:20] if reporter_name else '기자명 미제공'
        # NewsArticle 생성
        news_article = NewsArticle(
            id=uuid.UUID(article_id),
            title=(article_data.get('title') or '')[:255],
            url=(article_data.get('url') or '')[:225],
            published_at=published_at,
            summary_text=(article_data.get('content') or '')[:10000],
            male_audio_url="",
            female_audio_url="",
            category_name=(article_data.get('category') or '')[:30],
            original_image_url=(article_data.get('image_url') or '')[:200],
            thumbnail_image_url="",
            author=author,
            is_deleted=False,
            press_id=press.id,
            category_id=category.id
        )
        db.add(news_article)
        db.commit()
        db.refresh(news_article)
        # # TTS 생성 Celery 태스크
        # try:
        #     tts_task = generate_tts_audio_async_task(str(news_article.id))
        #     logger.info(f"TTS Celery 태스크 시작: {tts_task['task_id']}")
        # except Exception as e:
        #     logger.error(f"TTS Celery 태스크 시작 실패: {e}")
        # # 썸네일 이미지 생성 Celery 태스크
        # try:
        #     image_task = process_image_to_s3_async_task(str(news_article.id))
        #     logger.info(f"이미지 썸네일 생성 태스크 시작: {image_task['task_id']}")
        # except Exception as e:
        #     logger.error(f"이미지 썸네일 태스크 시작 실패: {e}")
        logger.info(f"기사 저장 완료: {news_article.title[:50]}...")
        return news_article
    except Exception as e:
        logger.error(f"기사 저장 실패: {e}")
        db.rollback()
    finally:
        db.close()
    return None


def save_articles_batch(db: Session, articles: List[Dict]) -> Dict[str, int]:
    """
    여러 기사를 일괄 저장
    Returns: 저장 결과 통계
    """
    saved_count = 0
    failed_count = 0
    duplicate_count = 0
    for article_data in articles:
        try:
            result = save_article_to_db(db, article_data)
            if result:
                saved_count += 1
            else:
                failed_count += 1
        except Exception as e:
            logger.error(f"기사 저장 중 오류: {e}")
            failed_count += 1
    return {
        'saved': saved_count,
        'failed': failed_count,
        'duplicate': duplicate_count,
        'total': len(articles)
    }