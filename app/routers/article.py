from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi import Request
from uuid import UUID
from app.core.database import get_db
from app.schemas.article import ArticleDetailResponse, ArticleRecentResponse, ArticleDeleteResponse
from app.schemas.article_recommend import ArticleRecommendResponse
from app.core.query import get_article_by_id, get_article_recent, get_articles_by_category_and_user_press, delete_article, mark_article_as_viewed
import redis
import json
from app.services.recommend.article_recommender import index_user_preferred_articles, recommend_articles_for_user_async
from app.services.recommend.opensearch import create_news_index

router = APIRouter(prefix="/articles",tags=["Articles"])

redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

#실시간 뉴스 가져오기 (20개)ㄴ
@router.get("/recent", response_model=List[ArticleRecentResponse])
def read_recent_articles(limit: int = 20, db: Session = Depends(get_db)):
    cache_key = f"recent_articles:{limit}"
    cached = redis_client.get(cache_key)
    if cached:
        return [ArticleRecentResponse(**{**a, "id": str(a["id"])}) for a in json.loads(cached)]
    articles = get_article_recent(db, limit)
    if not articles:
        raise HTTPException(status_code=404, detail="실시간 뉴스를 가져올 수 없습니다.")
    articles_data = [
        {
            "id": str(a.id),
            "title": a.title,
            "thumbnail_image_url": a.thumbnail_image_url,
            "category_name": a.category_name,
            "author": a.author,
            "published_at": a.published_at,
        }
        for a in articles
    ]
    redis_client.setex(cache_key, 60, json.dumps(articles_data, default=str))
    return [ArticleRecentResponse(**a) for a in articles_data]


#사용자 관심 카테고리 뉴스 가져오기
@router.get("/preferred-category", response_model=List[ArticleRecentResponse])
def get_articles_by_category_and_user_press_router(request: Request, category_name: str, db: Session = Depends(get_db)):
    user_id = request.state.user_id
    articles = get_articles_by_category_and_user_press(db, user_id, category_name)
    if not articles:
        raise HTTPException(status_code=404, detail="해당 조건에 맞는 기사가 없습니다.")
    
    import logging
    logging.info(f"📰 사용자 {user_id}의 {category_name} 카테고리 기사 {len(articles)}개 반환")
    
    return [
        ArticleRecentResponse(
            id=str(a.id),
            title=a.title,
            thumbnail_image_url=a.thumbnail_image_url,
            category_name=a.category_name,
            author=a.author,
            published_at=a.published_at,
            score=None
        )
        for a in articles
    ]

#키워드 관련 기사 조회
@router.get("/recommend", response_model=List[ArticleRecommendResponse])
async def recommend_articles(request: Request, db: Session = Depends(get_db)):
    user_id=request.state.user_id
    create_news_index()  # 인덱스가 없으면 생성, 있으면 무시
    await index_user_preferred_articles(db, user_id)  # 필터링 된 DB의 기사들을 OpenSearch에 인덱싱 (await 추가)
    results = await recommend_articles_for_user_async(db,user_id)
    if not results:
        raise HTTPException(status_code=404, detail="No articles found")
    
    import logging
    logging.info(f"🎯 사용자 {user_id}에게 추천 기사 {len(results)}개 반환")
    
    return [ArticleRecommendResponse(**r) for r in results]

#뉴스 상세 조회 하기
@router.get("/{article_id}", response_model=ArticleDetailResponse)
def get_article_detail(request: Request,article_id: UUID, db: Session = Depends(get_db)):
    user_id = request.state.user_id

    article = get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다.")
    # 읽음 기록 저장
    read_status = mark_article_as_viewed(db, user_id, article_id)
    if not read_status:
        raise HTTPException(status_code=400, detail="읽음 기록 저장 실패")
    return article

#기사 삭제하기
@router.delete("/{article_id}", response_model=ArticleDeleteResponse)
def delete_article_inform(article_id: str, db: Session = Depends(get_db)):
    result = delete_article(db, article_id)
    if result:
        return ArticleDeleteResponse(message="기사 삭제 완료", article_id=article_id)
    else:
        raise HTTPException(status_code=404, detail="삭제할 기사를 찾을 수 없습니다.")




    