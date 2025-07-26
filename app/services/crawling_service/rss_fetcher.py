import aiohttp
import xml.etree.ElementTree as ET
from typing import List

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

"""RSS 피드에서 기사 URL 목록 가져오기"""
async def fetch_rss_feed_async(session: aiohttp.ClientSession, rss_url: str) -> List[str]:
    try:
        async with session.get(rss_url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}")
            content = await response.text()
            root = ET.fromstring(content)
            # 기사 URL 목록 추출
            # 일단 각 URL당 10개만 추출하고 추후 수정 필요
            urls = []
            for i, item in enumerate(root.findall('.//item/link')):
                if i >= 20:
                    break
                if item.text:
                    urls.append(item.text)
            print(f"   🔍 추출된 URL 개수: {len(urls)}")
            return urls
    except Exception as e:
        print(f"❌ RSS 피드 요청 실패 {rss_url}: {e}")
        return []