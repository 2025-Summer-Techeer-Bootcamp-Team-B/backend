from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import time
from datetime import datetime
from sqlalchemy.orm import session
from app.schemas.article_recommend import ArticleResponse, UserKeywordRequest
from app.services.crawling_service.async_crawler import scrape_all_articles_async
from app.services.article_service.query import get_recent_articles
from app.core.database import SessionLocal, get_db
from app.services.recommend_service import recommend_articles_for_user, create_news_index, index_all_articles
from typing import List


router = APIRouter(prefix="/test",tags=["Test"])


@router.get("/crawl")
async def crawl_articles_async(save_to_db: bool = True):
    try:
        start_time = time.time()
        articles = await scrape_all_articles_async(max_concurrent=10, save_to_db=save_to_db)
        end_time = time.time()
        processing_time = end_time - start_time
        print(f"✅ API 비동기 크롤링 완료: {len(articles)}개 기사, {processing_time:.2f}초")
        return {
            "success": True,
            "articles": articles,
            "count": len(articles),
            "processing_time": f"{processing_time:.2f}초",
            "save_to_db": save_to_db,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ API 비동기 크롤링 실패: {e}")
        raise HTTPException(status_code=500, detail=f"크롤링 실패: {str(e)}")

"""저장된 최근 기사 20개 조회"""
@router.get("/recent_articles")
async def get_saved_articles(limit: int = 20, category: Optional[str] = None):
    try:
        db = SessionLocal()
        try:
            if category:
            #     articles = get_articles_by_category(db, category, limit)
            # else:
                articles = get_recent_articles(db, limit)
            
            # SQLAlchemy 객체를 딕셔너리로 변환
            articles_data = []
            for article in articles:
                article_dict = {
                    "id": str(article.id),
                    "title": article.title,
                    "url": article.url,
                    "summary_text": article.summary_text,
                    "categories": article.categories,
                    "image_url": article.image_url,
                    "author": article.author
                }
                
                # datetime 필드 안전하게 처리
                try:
                    if article.published_at:
                        article_dict["published_at"] = article.published_at.isoformat()
                    else:
                        article_dict["published_at"] = None
                except:
                    article_dict["published_at"] = None
                
                try:
                    if article.created_at:
                        article_dict["created_at"] = article.created_at.isoformat()
                    else:
                        article_dict["created_at"] = None
                except:
                    article_dict["created_at"] = None
                
                articles_data.append(article_dict)
            
            return {
                "success": True,
                "articles": articles_data,
                "count": len(articles_data),
                "category": category,
                "limit": limit
            }
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 기사 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"기사 조회 실패: {str(e)}") 


#키워드 관련 기사 조회
@router.post("/recommend", response_model=List[ArticleResponse])
def recommend_articles(req: UserKeywordRequest, db: session = Depends(get_db)):
    create_news_index()  # 인덱스가 없으면 생성, 있으면 무시
    index_all_articles(db)  # DB의 기사들을 OpenSearch에 인덱싱
    results = recommend_articles_for_user(req.user_id, db)
    if not results:
        raise HTTPException(status_code=404, detail="No articles found")
    return [ArticleResponse(**r) for r in results] 