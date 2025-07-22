import requests
from PIL import Image
from io import BytesIO
import boto3
from botocore.exceptions import ClientError
import uuid
from typing import Tuple, Optional, Dict
import os
from dotenv import load_dotenv

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

# image_url로 다운로드
def download_image(image_url: str) -> Optional[Image.Image]:
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
    if keep_aspect_ratio:
        width, height = image.size
        aspect_ratio = width / height
        new_width = size[0]
        new_height = int(new_width / aspect_ratio)
        return image.resize((new_width, new_height))
    else:
        return image.resize(size)
    
def create_thumbnail(image: Image.Image, size: Tuple[int, int] = (320, 200)) -> Image.Image:
    return resize_image(image, size, keep_aspect_ratio=True)

def image_to_bytes(image: Image.Image, format: str = 'JPEG', quality: int = 85) -> bytes:
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
    try:
        # S3 설정이 없는 경우 테스트용 URL 반환
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
        
        # S3 URL 반환
        return f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
    except ClientError as e:
        print(f"S3 업로드 실패: {e}")
        return None

def process_image_to_s3(image_url:str) -> Dict:

    image = download_image(image_url)

    if not image:
        result= "이미지 다운로드 실패"
        return result
    
    thumbnail = create_thumbnail(image)
    
    timestamp = str(uuid.uuid4())[:8]
    thumbnail_key = f"thumbnails/{timestamp}_thumb.jpg"
    thumbnail_bytes = image_to_bytes(thumbnail)

    return upload_to_s3(thumbnail_bytes,thumbnail_key,content_type="image/jpeg")