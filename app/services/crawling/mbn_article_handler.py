import aiohttp
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

SELECTORS = {
    "title": ['h2.news_ttl', 'h1.news_ttl', '.news_ttl'],
    "image": ['img[loading="lazy"]', '.thumb img', '.news_cnt_detail_wrap img'],
    "content": ['div.news_cnt_detail_wrap[itemprop="articleBody"]', '.news_cnt_detail_wrap'],
    "reporter": ['.news_write_info_group .author .name', '.author .name', '.reporter'],
    "published_time": ['.news_write_info_group .time_area .registration dd', '.time_area dd', '.registration dd'],
}

def get_image_url(soup: BeautifulSoup) -> Optional[str]:
    """MBN 뉴스 이미지 URL 추출"""
    for selector in SELECTORS['image']:
        img_tags = soup.select(selector)
        for img_tag in img_tags:
            src = img_tag.get('src')
            if src and isinstance(src, str) and src.strip():
                # MBN 이미지 도메인 확인
                if 'mk.co.kr' in src or 'pimg.mk.co.kr' in src:
                    if src.startswith('//'):
                        return f'https:{src}'
                    elif src.startswith('http'):
                        return src
                    else:
                        return f'https://www.mk.co.kr{src}' if src.startswith('/') else src
    return None

def select_one_text(soup: BeautifulSoup, selectors) -> Optional[str]:
    """여러 셀렉터 중 하나를 선택하여 텍스트 반환"""
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            return el.get_text(strip=True)
    return None

def get_content_text(soup: BeautifulSoup) -> Optional[str]:
    """MBN 뉴스 본문 텍스트 추출"""
    content_div = soup.select_one(SELECTORS['content'][0])  # 첫 번째 셀렉터 사용
    if content_div:
        # 광고 및 불필요한 요소 제거
        for tag in content_div(['script', 'style', '.ad_wrap', 'iframe']):
            tag.decompose()
        
        # 텍스트 추출
        text = content_div.get_text(separator=' ', strip=True)
        
        # 불필요한 텍스트 정리
        if text:
            # 광고 관련 텍스트 제거
            text = re.sub(r'MC_article_billboard_\d+', '', text)
            text = re.sub(r'google_ads_iframe.*', '', text)
            text = re.sub(r'Advertisement', '', text)
            text = re.sub(r'3rd party ad content', '', text)
            
            # 연속된 공백 정리
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text if len(text) > 20 else None
    return None

def get_reporter_name(soup: BeautifulSoup) -> Optional[str]:
    """MBN 뉴스 기자명 추출"""
    text = select_one_text(soup, SELECTORS['reporter'])
    if text:
        # "기자" 텍스트 제거
        text = text.replace('기자', '').strip()
        return text if text else None
    return None

"""MBN 뉴스 발행시간 추출"""
def get_published_time(soup: BeautifulSoup) -> Optional[str]:

    return select_one_text(soup, SELECTORS['published_time'])

"""MBN 뉴스 기사 추출 메인 함수"""
async def extract_mbn_article_async(session: aiohttp.ClientSession, url: str) -> Dict[str, Optional[str]]:
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}")
            
            html = await response.text()
            soup = BeautifulSoup(html, 'lxml')
            
            # 제목 추출
            title = select_one_text(soup, SELECTORS['title'])
            return {
                "title": title,
                "url": url,
                "image_url": get_image_url(soup),
                "content": get_content_text(soup),
                "published_time": get_published_time(soup),
                "reporter_name": get_reporter_name(soup),
            }
    except Exception as e:
        print(f"      ❌ MBN 기사 추출 중 예외 발생: {e}")
        return {
            "title": None,
            "url": None,
            "image_url": None,
            "content": None,
            "published_time": None,
            "reporter_name": None,
            "error": str(e)
        } 