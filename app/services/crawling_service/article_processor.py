"""기사 처리 및 요약"""
import asyncio
import aiohttp
from typing import Optional, Dict
from app.services.crawling_service.async_article_hankyung import extract_hankyung_article_async
from app.services.crawling_service.async_article_sbs import extract_sbs_article_async
from app.services.crawling_service.async_article_mbn import extract_mbn_article_async
from app.services.crawling_service.summarizer import summarize_article_with_gpt_async

async def process_article_with_summary(session: aiohttp.ClientSession, article_url: str, category: str, press: str, 
                                     article_index: int, total_articles: int) -> Optional[Dict]:
    try:
        # 언론사별 extractor 선택
        if press == "한국경제":
            details = await extract_hankyung_article_async(session, article_url)
        elif press == "SBS뉴스":
            details = await extract_sbs_article_async(session, article_url)
        elif press == "매일경제":
            details = await extract_mbn_article_async(session, article_url)
        else:
            print(f"   ⚠️ 지원하지 않는 언론사: {press}")
            return None

        if details and isinstance(details, dict):
            title = details.get('title')
            content = details.get('content')
            if title and content:
                # 카테고리 정보 추가
                details['category'] = category
                details['press_name'] = press
                # URL이 중복으로 들어가지 않도록 확인
                if details.get('url') != article_url:
                    details['url'] = article_url
                try:
                    summary = await summarize_article_with_gpt_async(content)  # 기사 요약 메서드 호출 (async)
                    if summary:
                        details['content'] = summary
                        print(f"   ✅ GPT 요약 완료")
                except Exception as summary_error:
                    print(f"   ❌ 요약 중 오류: {summary_error}")
                
                print(f"   ✅ 기사 추출 완료:")
                print(f"   " + "-" * 70)
                return details
            else:
                print(f"   ❌ 기사 내용 부족: {article_url}")
                return None
        else:
            print(f"   ❌ 기사 추출 실패: {article_url}")
            return None
            
    except Exception as e:
        print(f"   ❌ 기사 처리 실패 ({article_url}): {e}")
        return None