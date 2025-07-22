from typing import List
from uuid import UUID
from dotenv.main import logger
from sqlalchemy.orm import Session
from app.models.news_article import NewsArticle
from app.models.user_preferred_press import UserPreferredPress


# 실시간 뉴스 조회 20개까지
def get_article_recent(db: Session, limit: int = 20) -> List[NewsArticle]:
    return db.query(NewsArticle).filter(
        NewsArticle.is_deleted == False
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
