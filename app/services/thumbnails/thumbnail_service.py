import uuid
from typing import Dict
from app.core.database import get_db
from app.models.news_article import NewsArticle
from app.services.thumbnails.image_downloader import download_image
from app.services.thumbnails.image_processor import create_thumbnail, image_to_bytes
from app.services.thumbnails.gcs_uploader import upload_to_gcs

def process_image_to_gcs(article_id: str) -> Dict:
    """
    기사 ID로 DB에서 original_image_url을 조회해 썸네일을 생성하고 Google Cloud Storage에 업로드, DB에 URL 저장
    """
    db = next(get_db())
    try:
        article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
        if not article:
            return {"success": False, "error": "해당 article_id의 뉴스 기사가 존재하지 않습니다."}
        
        # 원본 이미지 URL이 없는 경우 fallback 이미지 사용
        if not article.original_image_url:
            return apply_fallback_image_direct(article_id)
        
        # 원본 이미지 다운로드
        image = download_image(article.original_image_url)
        if not image:
            # 이미지 다운로드 실패 시 fallback 이미지 사용
            return apply_fallback_image_direct(article_id)
        
        # 썸네일 생성
        thumbnail = create_thumbnail(image)
        timestamp = str(uuid.uuid4())[:8]
        thumbnail_key = f"thumbnails/{timestamp}_thumb.jpg"
        
        # 이미지를 바이트로 변환
        thumbnail_bytes = image_to_bytes(thumbnail)
        if not thumbnail_bytes:
            return {"success": False, "error": "이미지 바이트 변환 실패"}
        
        # GCS에 업로드
        thumbnail_url = upload_to_gcs(thumbnail_bytes, thumbnail_key, content_type="image/jpeg")
        if not thumbnail_url:
            return {"success": False, "error": "썸네일 Google Cloud Storage 업로드 실패"}
        
        # DB에 URL 저장
        article.thumbnail_image_url = thumbnail_url
        db.commit()
        db.refresh(article)
        
        return {
            "success": True, 
            "thumbnail_url": thumbnail_url,
            "method_used": "original"
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()

def apply_fallback_image_direct(article_id: str) -> Dict:
    """
    이미지 처리 없이 GCS의 fallback 이미지를 직접 적용합니다.
    """
    db = next(get_db())
    try:
        article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
        if not article:
            return {"success": False, "error": "해당 article_id의 뉴스 기사가 존재하지 않습니다."}
        
        # GCS fallback 이미지 URL 생성
        from app.services.thumbnails.gcs_uploader import GCS_BUCKET

        bucket_name = GCS_BUCKET or 'your-bucket-name'
        fallback_path = f"fallback/fallback_image.jpg"
        fallback_url = f"https://storage.googleapis.com/{bucket_name}/{fallback_path}"
        
        # DB에 fallback URL 저장
        article.thumbnail_image_url = fallback_url
        db.commit()
        db.refresh(article)
        
        return {
            "success": True,
            "thumbnail_url": fallback_url,
            "method_used": "fallback"
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()

def process_image_to_gcs_with_fallback(article_id: str) -> Dict:
    """
    기존 함수와의 호환성을 위한 별칭 함수
    """
    return process_image_to_gcs(article_id) 