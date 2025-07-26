import asyncio
import aiohttp
import time
from datetime import datetime
from typing import Dict, List
from app.services.article_service.save import save_articles_batch
from app.services.crawling_service.rss_fetcher import fetch_rss_feed_async
from app.core.database import SessionLocal
from app.services.crawling_service.article_processor import process_article_with_summary

RSS_FEEDS = {
    # "한국경제": {
    #     "증권": "https://www.hankyung.com/feed/finance",
    #     "경제": "https://www.hankyung.com/feed/economy",
    #     "부동산": "https://www.hankyung.com/feed/realestate",
    #     "IT": "https://www.hankyung.com/feed/it",
    #     "정치": "https://www.hankyung.com/feed/politics",
    #     "국제": "https://www.hankyung.com/feed/international",
    #     "사회": "https://www.hankyung.com/feed/society",
    #     "문화": "https://www.hankyung.com/feed/life",
    #     "스포츠": "https://www.hankyung.com/feed/sports",
    #     "연예": "https://www.hankyung.com/feed/entertainment"
    # },
    "SBS뉴스": {
        "정치": "https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER",
        "경제": "https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=02&plink=RSSREADER",
        "사회": "https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=03&plink=RSSREADER",
        "국제": "https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=07&plink=RSSREADER",
        "문화": "https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=08&plink=RSSREADER",
        "연예": "https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=14&plink=RSSREADER",
        "스포츠": "https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=09&plink=RSSREADER"
    },
    # "매일경제":{
    #     "경제":"https://www.mk.co.kr/rss/30100041",
    #     "정치":"https://www.mk.co.kr/rss/30200030",
    #     "사회":"https://www.mk.co.kr/rss/50400012",
    #     "국제":"https://www.mk.co.kr/rss/30300018",
    #     "증권":"https://www.mk.co.kr/rss/50200011",
    #     "부동산":"https://www.mk.co.kr/rss/50300009",
    #     "문화":"https://www.mk.co.kr/rss/30000023",
    #     "스포츠":"https://www.mk.co.kr/rss/71000001",
    #     "IT":"https://www.mk.co.kr/rss/50700001"
    # },
}

def print_section(title: str):
    print("=" * 80)
    print(title)
    print("=" * 80)

async def scrape_category_async(
    session: aiohttp.ClientSession,
    category: str,
    rss_url: str,
    press: str,
    semaphore: asyncio.Semaphore
) -> List[Dict]:
    """
    카테고리별 비동기 크롤링 (동시성 제한)
    """
    print(f"📰 {press} - {category} 카테고리 크롤링 중...")
    start_time = time.time()
    article_urls = await fetch_rss_feed_async(session, rss_url)
    if not article_urls:
        print(f"   ❌ {category} 카테고리에서 기사를 찾을 수 없습니다.")
        return []
    print(f"   📊 {category} 카테고리: {len(article_urls)}개 기사 발견")
    async def process_with_semaphore(url, index):
        async with semaphore:
            await asyncio.sleep(0.5)  # 서버 부하 방지
            return await process_article_with_summary(session, url, category, press, index, len(article_urls))
    tasks = [process_with_semaphore(url, i + 1) for i, url in enumerate(article_urls)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    successful_articles = [r for r in results if r and not isinstance(r, Exception) and isinstance(r, dict)]
    elapsed = time.time() - start_time
    print(f"   🎯 {category} 완료: {len(successful_articles)}개 성공 (소요시간: {elapsed:.1f}초)")
    print("   " + "-" * 70)
    return successful_articles

async def scrape_all_articles_async(max_concurrent: int = 10, save_to_db: bool = True):
    """
    전체 언론사/카테고리 비동기 크롤링 및 DB 저장
    """
    scraped_articles = []
    start_time = time.time()
    processed_articles = 0
    failed_articles = 0
    print_section(f"🚀 크롤링 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⚡ 동시 처리 수: {max_concurrent}")
    semaphore = asyncio.Semaphore(min(max_concurrent, 10))
    connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        category_tasks = [
            scrape_category_async(session, category, rss_url, press, semaphore)
            for press, categories in RSS_FEEDS.items()
            for category, rss_url in categories.items()
        ]
        category_results = await asyncio.gather(*category_tasks, return_exceptions=True)
        for result in category_results:
            if isinstance(result, Exception):
                print(f"❌ 카테고리 처리 실패: {result}")
                failed_articles += 1
            elif isinstance(result, list):
                scraped_articles.extend(result)
                processed_articles += len(result)
    total_time = time.time() - start_time
    success_rate = (processed_articles / (processed_articles + failed_articles) * 100) if (processed_articles + failed_articles) > 0 else 0
    print_section(f"🎉 비동기 크롤링 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 전체 통계:")
    print(f"   • 성공: {processed_articles}개")
    print(f"   • 실패: {failed_articles}개")
    print(f"   • 성공률: {success_rate:.1f}%")
    print(f"   • 총 소요시간: {total_time:.1f}초 ({total_time/60:.1f}분)")
    if processed_articles > 0:
        print(f"   • 평균 처리시간: {total_time/processed_articles:.1f}초/기사")
    else:
        print(f"   • 평균 처리시간: 계산 불가")
    if scraped_articles and save_to_db:
        print("\n💾 데이터베이스 저장 시작...")
        db = SessionLocal()
        try:
            save_result = save_articles_batch(db, scraped_articles)
            print(f"📊 데이터베이스 저장 결과:")
            print(f"   • 저장 성공: {save_result['saved']}개")
        except Exception as e:
            print(f"❌ 데이터베이스 저장 실패: {e}")
        finally:
            db.close()
    elif scraped_articles and not save_to_db:
        print("\n💾 데이터베이스 저장 건너뜀 (save_to_db=False)")
    return scraped_articles