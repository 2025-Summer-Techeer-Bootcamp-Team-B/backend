from sqlalchemy.orm import Session
from app.models.article_history import ArticleHistory
from app.models.news_article import NewsArticle
from app.models.category import Category

def get_user_history(user_id: str, db: Session):
    return db.query(ArticleHistory).join(
        NewsArticle, ArticleHistory.news_id == NewsArticle.id
    ).join(
        Category, NewsArticle.category_id == Category.id
    ).filter(
        ArticleHistory.user_id == user_id,
        ArticleHistory.is_deleted == False,
        NewsArticle.is_deleted == False
    ).order_by(
        Category.category_name.asc(),
        ArticleHistory.viewed_at.desc()
    ).all()