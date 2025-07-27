import datetime
from typing import List
from uuid import UUID
from dotenv.main import logger
from sqlalchemy.orm import Session
from app.models.article_history import ArticleHistory
from app.models.news_article import NewsArticle
from app.models.user_preferred_press import UserPreferredPress
from app.core.save import KST
from app.models.user_preferred_press import UserPreferredPress
from app.models.user_category import UserCategory
from app.utils.datetime_utils import get_today_range_kst


# 실시간 뉴스 조회 20개까지
def get_article_recent(db: Session, limit: int = 20) -> List[NewsArticle]:
    # 모든 주요 필드가 None/빈 문자열이 아닌 기사만 반환
    return db.query(NewsArticle).filter(
        NewsArticle.is_deleted == False,
        NewsArticle.title.isnot(None), NewsArticle.title != '',
        NewsArticle.url.isnot(None), NewsArticle.url != '',
        NewsArticle.published_at.isnot(None),
        NewsArticle.summary_text.isnot(None), NewsArticle.summary_text != '',
        NewsArticle.male_audio_url.isnot(None), NewsArticle.male_audio_url != '',
        NewsArticle.female_audio_url.isnot(None), NewsArticle.female_audio_url != '',
        NewsArticle.original_image_url.isnot(None), NewsArticle.original_image_url != '',
        NewsArticle.thumbnail_image_url.isnot(None), NewsArticle.thumbnail_image_url != '',
        NewsArticle.author.isnot(None), NewsArticle.author != '',
        NewsArticle.category_name.isnot(None), NewsArticle.category_name != ''
    ).order_by(NewsArticle.published_at.desc()).limit(limit).all()

# 뉴스 상세 조회
def get_article_by_id(db: Session, article_id: UUID):
    return db.query(NewsArticle).filter(NewsArticle.id == article_id).first()

# 사용자 관심 카테고리 기사 조회
def get_articles_by_category_and_user_press(db: Session, user_id: str, category_name: str):
    preferred_press_ids = (
        db.query(UserPreferredPress.press_id)
        .filter(
            UserPreferredPress.user_id == user_id,
            UserPreferredPress.is_deleted == False
        )
        .subquery()
    )
    articles = (
        db.query(NewsArticle)
        .filter(
            NewsArticle.category_name == category_name,
            NewsArticle.press_id.in_(preferred_press_ids),
            NewsArticle.is_deleted == False
        )
        .order_by(NewsArticle.published_at.desc())
        .all()
    )
    return articles

# 기사 삭제 
def delete_article(db: Session, article_id: str) -> bool:
    try:
        article = db.query(NewsArticle).filter(
            NewsArticle.id == UUID(article_id),
            NewsArticle.is_deleted == False
        ).first()
        if article:
            article.is_deleted = True
            db.commit()
            return True
        else:
            return False
    except Exception:
        db.rollback()
        return False

#   사용자가 기사를 읽으면 ArticleHistory에 viewed_at을 KST로 기록
def mark_article_as_viewed(db: Session, user_id: str, article_id: str) -> bool:
    now = datetime.datetime.now(KST)
    try:
        history = db.query(ArticleHistory).filter(
            ArticleHistory.user_id == user_id,
            ArticleHistory.news_id == article_id,
            ArticleHistory.is_deleted == False
        ).first()
        if history:
            history.viewed_at = now
            db.commit()
            db.refresh(history)
            return True
        new_history = ArticleHistory(
            user_id=user_id,
            news_id=article_id,
            viewed_at=now,
            is_deleted=False
        )
        db.add(new_history)
        db.commit()
        db.refresh(new_history)
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"기사 읽음 처리 실패: {e}")
        return False

def get_user_preferred_articles(db: Session, user_id: str) -> List[NewsArticle]:
    """
    사용자가 지정한 언론사와 관심 카테고리의 '오늘' 기사만 반환
    """
    # 1. 사용자의 선호 언론사 id 목록
    press_ids = db.query(UserPreferredPress.press_id).filter(
        UserPreferredPress.user_id == user_id,
        UserPreferredPress.is_deleted == False
    ).all()
    press_ids = [pid[0] for pid in press_ids]
    # 2. 사용자의 관심 카테고리 id 목록
    category_ids = db.query(UserCategory.category_id).filter(
        UserCategory.user_id == user_id,
        UserCategory.is_deleted == False
    ).all()
    category_ids = [cid[0] for cid in category_ids]
    # 3. 오늘 날짜 범위
    start, end = get_today_range_kst()
    # 4. 해당 언론사+카테고리+오늘 기사만 반환
    articles = db.query(NewsArticle).filter(
        NewsArticle.press_id.in_(press_ids),
        NewsArticle.category_id.in_(category_ids),
        NewsArticle.is_deleted == False,
        NewsArticle.published_at >= start,
        NewsArticle.published_at < end
    ).order_by(NewsArticle.published_at.desc()).all()
    return articles

