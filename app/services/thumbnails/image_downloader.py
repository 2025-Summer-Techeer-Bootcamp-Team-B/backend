import requests
from PIL import Image
from io import BytesIO
from typing import Optional

def download_image(image_url: str) -> Optional[Image.Image]:
    """이미지 URL에서 이미지를 다운로드합니다."""
    try:
        if not image_url:
            return None
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        return image
    except Exception as e:
        print(f"이미지 다운로드 실패: {e}")
        return None 