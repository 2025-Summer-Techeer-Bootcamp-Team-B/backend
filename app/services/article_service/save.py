from sqlalchemy.orm import Session
from app.models.news_article import NewsArticle
from app.models.press import Press
from typing import Dict, List, Optional
import datetime
import uuid
import logging
import hashlib
import os
from dateutil import parser
import logging
from app.celery_app import generate_tts_audio_async_task
from app.models.category import Category
logger = logging.getLogger(__name__)

# generate_audio_urls 함수 삭제됨

def save_article_to_db(db: Session, article_data: Dict) -> Optional[NewsArticle]:
    """
    크롤링한 기사 데이터를 데이터베이스에 저장
    
    Args:
        db: 데이터베이스 세션
        article_data: 크롤링된 기사 데이터
    
    Returns:
        저장된 NewsArticle 객체 또는 None (실패 시)
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
        
        # 언론사 ID 찾기 (press_name을 article_data에서 가져옴, 없으면 'unknown')
        press_name = article_data.get('press_name', 'unknown')
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


    
        # 발행 시간 파싱
        published_at = parse_published_time(article_data.get('published_time'))
        if not published_at:
            published_at = datetime.datetime.now(datetime.timezone.utc)
        
        # 기사 ID 생성
        article_id = str(uuid.uuid4())
        
        # 카테고리 찾기 또는 생성
        category_name = article_data.get('category') or ''
        category = db.query(Category).filter(Category.category_name == category_name).first()
        if not category:
            category = Category(category_name=category_name)
            db.add(category)
            db.commit()
            db.refresh(category)
        # NewsArticle 객체 생성 (오디오 URL은 빈 값으로)
        news_article = NewsArticle(
            id=uuid.UUID(article_id),
            title=(article_data.get('title') or '')[:255],  # 길이 제한
            url=(article_data.get('url') or '')[:225],      # 길이 제한
            published_at=published_at,
            summary_text=(article_data.get('content') or '')[:10000],  # 텍스트 길이 제한
            male_audio_url="",
            female_audio_url="",
            cetagory_name=category_name[:30],  # 필드명 및 길이 수정
            original_image_url=(article_data.get('image_url') or '')[:200], # 모델 필드명에 맞게
            thumbnail_image_url=None,  # 필요시 값 할당
            author=(article_data.get('reporter_name') or '')[:20], # 길이 제한
            is_deleted=False,
            press_id=press.id,
            category_id=category.id  # 반드시 실제 카테고리 ID 할당
        )
        
        # 데이터베이스에 저장
        db.add(news_article)
        db.commit()
        db.refresh(news_article)
        
        # TTS 오디오 생성 태스크 시작
        try:
            tts_task = generate_tts_audio_async_task(str(news_article.id))
            logger.info(f"TTS 오디오 생성 태스크 시작: {tts_task['task_id']}")
        except Exception as e:
            logger.error(f"TTS 태스크 시작 실패: {e}")
        
        logger.info(f"기사 저장 완료: {news_article.title[:50]}...")
        return news_article
        
    except Exception as e:
        logger.error(f"기사 저장 실패: {e}")
        db.rollback()
        return None

def save_articles_batch(db: Session, articles: List[Dict]) -> Dict[str, int]:
    """
    여러 기사를 일괄 저장
    
    Args:
        db: 데이터베이스 세션
        articles: 크롤링된 기사 데이터 리스트
    
    Returns:
        저장 결과 통계
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


KST = datetime.timezone(datetime.timedelta(hours=9))

def parse_published_time(time_str: Optional[str]) -> datetime.datetime:
    """
    발행 시간 문자열을 datetime 객체로 파싱하고 KST(Asia/Seoul)로 변환합니다.

    Args:
        time_str (Optional[str]): 발행 시간 문자열

    Returns:
        datetime.datetime: KST 타임존이 적용된 datetime 객체
    """
    if not time_str:
        return datetime.datetime.now(KST)

    try:
        dt = parser.parse(time_str)

        # 타임존 정보가 없으면 UTC로 간주
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)

        # KST로 변환 후 반환
        return dt.astimezone(KST)

    except Exception as e:
        logger.warning(f"시간 파싱 실패: {time_str} ({e})")
        return datetime.datetime.now(KST)



