import os
from typing import Optional
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()

GCS_BUCKET = os.getenv('GOOGLE_CLOUD_STORAGE_BUCKET', 'your-bucket-name')

storage_client = storage.Client()
bucket = storage_client.bucket(GCS_BUCKET)

def upload_to_gcs(image_bytes: bytes, gcs_key: str, content_type: str = 'image/jpeg') -> Optional[str]:
    """이미지 바이트를 Google Cloud Storage에 업로드하고 URL 반환"""
    try:
        if not GCS_BUCKET:
            print("Google Cloud Storage 버킷이 설정되지 않아서 테스트용 URL을 반환합니다.")
            return f"https://test-gcs.example.com/{gcs_key}"
        
        blob = bucket.blob(gcs_key)
        blob.upload_from_string(
            image_bytes,
            content_type=content_type
        )
        
        # 캐시 컨트롤 설정
        blob.cache_control = 'max-age=31536000'
        blob.patch()
        
        return f"https://storage.googleapis.com/{GCS_BUCKET}/{gcs_key}"
    except Exception as e:
        print(f"Google Cloud Storage 업로드 실패: {e}")
        return None 