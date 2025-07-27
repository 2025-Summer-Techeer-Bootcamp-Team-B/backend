import aiohttp
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

SELECTORS = {
    # 실제 기사에서 가장 많이 쓰이는 구조 위주로 정리
    "title": [
        'h1.headline',
        '.headline h1',
        'h1.title',
        'h1',
    ],
    "image": [
        '.article-img img',
        '.main-img img',
        '.content-img img',
        '.article-content img',
        '.article-body img',
        '.content img',
        'img[alt*="기사"]',
        'img[alt*="사진"]',
        'img[alt*="이미지"]',
    ],
    "content": [
        '.article-content',
        '.article-body',
        '.main-content',
        '.content',
        '.article',
        '.article-detail',
    ],
    "time": [
        '.txt-date',
        '.date',
        'time',
    ],
    "reporter": [
        '.reporter',
        '.author',
        '.byline',
    ]
}

def select_one_text(soup: BeautifulSoup, selectors) -> Optional[str]:
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            return el.get_text(strip=True)
    return None

""" "입력" 텍스트 제거하고 날짜/시간만 반환"""
def select_time_text(soup: BeautifulSoup, selectors) -> Optional[str]:
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            time_text = el.get_text(strip=True)
            if time_text:

                time_text = time_text.replace('입력', '').strip()
                if time_text:
                    return time_text
    
    # 백업: .item 클래스에서 txt-date 찾기
    item_elements = soup.select('.item')
    for item in item_elements:
        txt_date = item.select_one('.txt-date')
        if txt_date:
            time_text = txt_date.get_text(strip=True)
            if time_text:
                return time_text
    return None

"""이미지 URL 추출 - 기사 관련 이미지만 찾기"""
def select_image_url(soup: BeautifulSoup, selectors) -> Optional[str]:
    for sel in selectors:
        elements = soup.select(sel)
        for el in elements:
            # 1. srcset 우선
            srcset = el.get('srcset') or el.get('data-srcset')
            if srcset:
                if not isinstance(srcset, str):
                    srcset = ' '.join(srcset)
                candidates = [s.strip().split(' ')[0] for s in srcset.split(',') if s.strip()]
                if candidates:
                    src = candidates[-1]
                    if src.startswith('//'):
                        return f'https:{src}'
                    elif src.startswith('http'):
                        return src
                    else:
                        return f'https://img.hankyung.com{src}' if src.startswith('/') else src
            # 2. data-src
            data_src = el.get('data-src')
            if data_src and isinstance(data_src, str) and data_src.strip():
                if data_src.startswith('//'):
                    return f'https:{data_src}'
                elif data_src.startswith('http'):
                    return data_src
                else:
                    return f'https://img.hankyung.com{data_src}' if data_src.startswith('/') else data_src
            # 3. src
            src = el.get('src')
            if src and isinstance(src, str) and src.strip():
                if src.startswith('//'):
                    return f'https:{src}'
                elif src.startswith('http'):
                    return src
                else:
                    return f'https://img.hankyung.com{src}' if src.startswith('/') else src
            # 4. onerror 대체 이미지 경로 파싱
            onerror = el.get('onerror')
            if onerror:
                import re
                onerror_str = str(onerror)
                match = re.search(r'this\.src=([\"\"][^\"\"]+[\"\"]|\'[^\']+\')', onerror_str)
                if match:
                    alt_src = match.group(1).strip('"').strip("'")
                    if alt_src.startswith('//'):
                        return f'https:{alt_src}'
                    elif alt_src.startswith('http'):
                        return alt_src
                    else:
                        return f'https://img.hankyung.com{alt_src}' if alt_src.startswith('/') else alt_src
    return None

"""불필요한 텍스트 제거 (간략 버전)"""
def clean_content_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    patterns = [
        r'\[[^\]]*\]', r'\([^)]*\)', r'기자\s*=\s*[^\n]*', r'▶\s*[^\n]*',
        r'입력\s*:?\s*[^\n]*', r'수정\s*:?\s*[^\n]*', r'한국경제\s*[^\n]*',
        r'ⓒ\s*한경닷컴.*', r'무단전재.*', r'Copyright.*', r'이 기사는.*',
    ]
    for pat in patterns:
        text = re.sub(pat, '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text if len(text) > 10 else None

def extract_main_content(soup: BeautifulSoup, selectors) -> Optional[str]:
    for sel in selectors:
        content_div = soup.select_one(sel)
        if content_div:
            # Remove script/style/ads
            for tag in content_div(['script', 'style', 'iframe', '.ad_wrap', '.advertisement', '.ad', '.banner']):
                tag.decompose()
            text = content_div.get_text(separator=' ', strip=True)
            cleaned = clean_content_text(text)
            if cleaned:
                return cleaned
    return None

def get_reporter_name(soup: BeautifulSoup, selectors) -> Optional[str]:
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            text = el.get_text(strip=True)
            text = re.sub(r'기자.*', '', text).strip()
            return text if text else None
    return None

"""비동기로 한국경제 기사 추출"""
async def extract_hankyung_article_async(session: aiohttp.ClientSession, url: str) -> Dict[str, Optional[str]]:
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}")
            html = await response.text()
            soup = BeautifulSoup(html, 'lxml')
            return {
                "title": select_one_text(soup, SELECTORS['title']),
                "url": url,
                "image_url": select_image_url(soup, SELECTORS['image']),
                "content": extract_main_content(soup, SELECTORS['content']),
                "published_time": select_time_text(soup, SELECTORS['time']),
                "reporter_name": get_reporter_name(soup, SELECTORS['reporter']),
            }
    except Exception as e:
        print(f"      ❌ 기사 추출 중 예외 발생: {e}")
        return {
            "title": None,
            "url": None,
            "image_url": None,
            "content": None,
            "published_time": None,
            "reporter_name": None,
            "error": str(e)
        } 