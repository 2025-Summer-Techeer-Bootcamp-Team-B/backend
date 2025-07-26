import os
import uuid
import requests
from PIL import Image
from io import BytesIO
from typing import Tuple, Optional, Dict
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from app.core.database import get_db
from app.models.news_article import NewsArticle

load_dotenv()

S3_BUCKET = os.getenv('AWS_S3_BUCKET', 'your-bucket-name')
S3_REGION = os.getenv('AWS_REGION', 'ap-northeast-2')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=S3_REGION
)

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

def resize_image(image: Image.Image, size: Tuple[int, int], keep_aspect_ratio: bool = True) -> Image.Image:
    """이미지 크기 조정 (비율 유지 옵션)"""
    if keep_aspect_ratio:
        width, height = image.size
        aspect_ratio = width / height
        new_width = size[0]
        new_height = int(new_width / aspect_ratio)
        return image.resize((new_width, new_height))
    else:
        return image.resize(size)

def create_thumbnail(image: Image.Image, size: Tuple[int, int] = (320, 200)) -> Image.Image:
    """이미지에서 썸네일 생성"""
    return resize_image(image, size, keep_aspect_ratio=True)

def image_to_bytes(image: Image.Image, format: str = 'JPEG', quality: int = 85) -> Optional[bytes]:
    """PIL 이미지를 바이트로 변환"""
    try:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        buffer = BytesIO()
        image.save(buffer, format=format, quality=quality, optimize=True)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        print(f"이미지 변환 실패: {e}")
        return None

def upload_to_s3(image_bytes: bytes, s3_key: str, content_type: str = 'image/jpeg') -> Optional[str]:
    """이미지 바이트를 S3에 업로드하고 URL 반환"""
    try:
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            print("AWS 설정이 없어서 테스트용 URL을 반환합니다.")
            return f"https://test-s3.example.com/{s3_key}"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=image_bytes,
            ContentType=content_type,
            CacheControl='max-age=31536000'
        )
        return f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
    except ClientError as e:
        print(f"S3 업로드 실패: {e}")
        return None

def process_image_to_s3(article_id: str) -> Dict:
    """
    기사 ID로 DB에서 original_image_url을 조회해 썸네일을 생성하고 S3에 업로드, DB에 URL 저장
    """
    db = next(get_db())
    try:
        article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
        if not article or not article.original_image_url:
            return {"success": False, "error": "해당 article_id의 뉴스 기사가 존재하지 않거나 이미지 URL이 없습니다."}
        image = download_image(article.original_image_url)
        if not image:
            return {"success": False, "error": "이미지 다운로드 실패"}
        thumbnail = create_thumbnail(image)
        timestamp = str(uuid.uuid4())[:8]
        thumbnail_key = f"thumbnails/{timestamp}_thumb.jpg"
        thumbnail_bytes = image_to_bytes(thumbnail)
        if not thumbnail_bytes:
            return {"success": False, "error": "이미지 바이트 변환 실패"}
        thumbnail_url = upload_to_s3(thumbnail_bytes, thumbnail_key, content_type="image/jpeg")
        if not thumbnail_url:
            return {"success": False, "error": "썸네일 S3 업로드 실패"}
        article.thumbnail_image_url = thumbnail_url
        db.commit()
        db.refresh(article)
        return {"success": True, "thumbnail_url": thumbnail_url}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()