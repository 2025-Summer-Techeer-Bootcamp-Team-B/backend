# routers 패키지 초기화 파일 
from fastapi import APIRouter
from .article import router as article_router
from .async_crawl_router import router as async_crawl_router
from .auth import router as auth_router
from .chat import router as chat_bot_router
from .user import router as user_router
router = APIRouter(prefix="/api/v1")  # ✅ 여기에서 공통 prefix 적용


router.include_router(article_router)
router.include_router(async_crawl_router)
router.include_router(auth_router)
router.include_router(chat_bot_router)
router.include_router(user_router)