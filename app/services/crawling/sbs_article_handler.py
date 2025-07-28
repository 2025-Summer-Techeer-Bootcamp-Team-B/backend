import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Optional

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

SELECTORS = {
    "title": ['h1.article_main_tit#news-title', 'h1.article_main_tit', '.article_main_tit', 'h1'],
    "image": ['img', 'img.mainimg', '.mainimg img', '.article_img img', '.content_img img'],
    "content": ['div.text_area[itemprop="articleBody"]', '.text_area', '.article_content', '.content'],
    "reporter": ['span[itemprop="name"]', '.reporter', '.author', '.byline'],
    "published_time": ['div.date_area span', '.date_area span', '.date span', 'time'],
    "published_meta": ['div.date_area meta[itemprop="datePublished"]', 'meta[itemprop="datePublished"]'],
}

def select_one_text(soup: BeautifulSoup, selectors) -> Optional[str]:
    """여러 셀렉터 중 하나를 선택하여 텍스트 반환"""
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            return el.get_text(strip=True)
    return None

def extract_valid_url(img_tag) -> Optional[str]:
    """
    img 태그에서 유효한 이미지 URL 추출 (data:로 시작하는 base64는 무시)
    """
    srcset = img_tag.get('srcset') or img_tag.get('data-srcset')
    if srcset:
        if not isinstance(srcset, str):
            srcset = ' '.join(srcset)
        candidates = [s.strip().split(' ')[0] for s in srcset.split(',') if s.strip()]
        candidates = [c for c in candidates if not c.startswith('data:')]
        for src in reversed(candidates):
            if src.startswith('data:'):
                continue
            if src.startswith('//'):
                return f'https:{src}'
            elif src.startswith('http'):
                return src
            elif src.startswith('/'):
                return f'https://img.sbs.co.kr{src}'
    src = img_tag.get('src')
    if isinstance(src, str) and src.strip() and not src.startswith('data:'):
        if src.startswith('//'):
            return f'https:{src}'
        elif src.startswith('http'):
            return src
        elif src.startswith('/'):
            return f'https://img.sbs.co.kr{src}'
    return None

def get_image_url(soup: BeautifulSoup) -> Optional[str]:
    """
    SBS 기사에서 대표 이미지를 추출한다.
    - srcset, data-srcset, src 속성에서 'data:'로 시작하는 값은 무시
    - http(s):// 또는 //로 시작하는 외부 이미지 URL만 반환
    """
    for selector in SELECTORS['image']:
        img_tag = soup.select_one(selector)
        if img_tag:
            url = extract_valid_url(img_tag)
            if url and not url.startswith('data:'):
                return url
    for img_tag in soup.find_all('img'):
        url = extract_valid_url(img_tag)
        if url and not url.startswith('data:'):
            return url
    return None

def get_content_text(soup: BeautifulSoup) -> Optional[str]:
    """
    기사 본문 텍스트 추출. 여러 셀렉터를 순회하며, script/style 태그 제거 후 20자 이상만 반환.
    """
    for selector in SELECTORS['content']:
        content_div = soup.select_one(selector)
        if content_div:
            for tag in content_div(['script', 'style']):
                tag.decompose()
            text = content_div.get_text(separator=' ', strip=True)
            if isinstance(text, str) and len(text) > 20:
                return text
    return None

def get_published_time(soup: BeautifulSoup) -> Optional[str]:
    """
    기사 발행 시각 추출. meta 태그 우선, 없으면 가시 텍스트.
    """
    for meta_selector in SELECTORS['published_meta']:
        meta = soup.select_one(meta_selector)
        if meta and meta.has_attr('content'):
            content_val = meta['content']
            if isinstance(content_val, str):
                return content_val
    return select_one_text(soup, SELECTORS['published_time'])

def get_reporter_name(soup: BeautifulSoup) -> Optional[str]:
    """
    기자명 추출. span[itemprop="name"] > .reporter span > .reporter 내 '기자' 포함 텍스트 순.
    """
    span = soup.select_one('span[itemprop="name"]')
    if span:
        name = span.get_text(strip=True)
        if name:
            return name
    span = soup.select_one('.reporter span')
    if span:
        name = span.get_text(strip=True)
        if name:
            return name
    reporter = soup.select_one('.reporter')
    if reporter:
        text = reporter.get_text(strip=True)
        if '기자' in text:
            return text
    return None

async def extract_sbs_article_async(session: aiohttp.ClientSession, url: str) -> Dict[str, Optional[str]]:
    """
    SBS 뉴스 기사 URL에서 주요 정보(제목, 이미지, 본문, 발행일, 기자명 등) 비동기 추출
    """
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}")
            html = await response.text()
            soup = BeautifulSoup(html, 'lxml')
            return {
                "title": select_one_text(soup, SELECTORS['title']),
                "url": url,
                "image_url": get_image_url(soup),
                "content": get_content_text(soup),
                "published_time": get_published_time(soup),
                "reporter_name": get_reporter_name(soup),
            }
    except Exception as e:
        print(f"      ❌ SBS 기사 추출 중 예외 발생: {e}")
        return {
            "title": None,
            "url": None,
            "image_url": None,
            "content": None,
            "published_time": None,
            "reporter_name": None,
            "error": str(e)
        }
