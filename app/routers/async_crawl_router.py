from fastapi import APIRouter, HTTPException
from typing import Optional
import time
from datetime import datetime
from app.core.database import SessionLocal
from app.services.crawling_service.async_crawler import scrape_all_articles_async
from app.schemas.news_crawl import NewsCrawlResponse, NewsCrawledArticle

router = APIRouter(prefix="/test",tags=["Test"])

@router.get("/crawl", response_model=NewsCrawlResponse)
async def crawl_articles_async(save_to_db: bool = True):
    try:
        start_time = time.time()
        articles = await scrape_all_articles_async(max_concurrent=10, save_to_db=save_to_db)
        end_time = time.time()
        processing_time = end_time - start_time
        print(f"✅ API 비동기 크롤링 완료: {len(articles)}개 기사, {processing_time:.2f}초")
        return NewsCrawlResponse(
            success=True,
            articles=[NewsCrawledArticle(**a) for a in articles],
            count=len(articles),
            processing_time=f"{processing_time:.2f}초",
            save_to_db=save_to_db,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        print(f"❌ API 비동기 크롤링 실패: {e}")
        raise HTTPException(status_code=500, detail=f"크롤링 실패: {str(e)}")