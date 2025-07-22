from fastapi import APIRouter, HTTPException, Depends
from app.services.article_service.query import get_article_by_id
from app.services.article_service.image_process import process_image_to_s3
from app.celery_app import process_image_to_s3_async_task
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.schemas.image_processor import ImageProcessRequest, ImageProcessResponse

router = APIRouter(prefix="/image", tags=["image"])

@router.post("/process", response_model=ImageProcessResponse)
async def process_image_endpoint(request: ImageProcessRequest, db: Session = Depends(get_db)):
    try:
        # 기사 존재 확인
        article = get_article_by_id(db, request.article_id)
        if not article:
            raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다")
        
        # 이미지 URL 확인
        if not article.original_image_url:
            raise HTTPException(status_code=400, detail="기사에 이미지 URL이 없습니다")
        
        # 비동기로 이미지 처리 시작
        result = process_image_to_s3_async_task(request.article_id)
        
        return ImageProcessResponse(
            message="이미지 처리가 백그라운드에서 시작되었습니다",
            task_id=result["task_id"],
            status=result["status"],
            article_id=request.article_id
        )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")