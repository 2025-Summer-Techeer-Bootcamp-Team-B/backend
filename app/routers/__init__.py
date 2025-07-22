# routers 패키지 초기화 파일 
from fastapi import APIRouter
from .article import router as article_router
from .async_crawl_router import router as async_crawl_router
from .user import router as user_router
from .image_processor import router as image_processor_router
from .user_setting import router as user_setting_router
from .chat_bot import router as chat_bot_router
router = APIRouter(prefix="/api/v1")  # ✅ 여기에서 공통 prefix 적용


router.include_router(article_router)
router.include_router(async_crawl_router)
router.include_router(user_router)
router.include_router(image_processor_router)
router.include_router(user_setting_router)
router.include_router(chat_bot_router)