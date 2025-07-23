from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.schemas.article import ArticleDetailResponse, ArticleRecentResponse, ArticleDeleteResponse
from app.services.article_service.query import get_article_by_id, get_article_recent, get_articles_by_category_and_user_press, delete_article

router = APIRouter(prefix="/articles",tags=["Articles"])

#실시간 뉴스 가져오기 (20개)
@router.get("/recent", response_model=List[ArticleRecentResponse])
def read_recent_articles(limit: int = 20, db: Session = Depends(get_db)):
    articles = get_article_recent(db, limit)
    if not articles:
        raise HTTPException(status_code=404, detail="실시간 뉴스를 가져올 수 없습니다.")
    return articles
#뉴스 상세 조회 하기
@router.get("/{article_id}", response_model=ArticleDetailResponse)
def get_article_detail(article_id: UUID, db: Session = Depends(get_db)):
    article = get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다.")
    return article


#사용자 관심 카테고리 뉴스 가져오기
@router.get("/preference_category_article", response_model=List[ArticleRecentResponse])
def get_articles_by_category_and_user_press_router(user_id: str, category_name: str, db: Session = Depends(get_db)):
    articles = get_articles_by_category_and_user_press(db, user_id, category_name)
    if not articles:
        raise HTTPException(status_code=404, detail="해당 조건에 맞는 기사가 없습니다.")
    return articles

#기사 삭제하기
@router.delete("/{article_id}", response_model=ArticleDeleteResponse)
def delete_article_inform(article_id: str, db: Session = Depends(get_db)):
    result = delete_article(db, article_id)
    if result:
        return ArticleDeleteResponse(message="기사 삭제 완료", article_id=article_id)
    else:
        raise HTTPException(status_code=404, detail="삭제할 기사를 찾을 수 없습니다.")
    