from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.auth.jwt_utils import verify_token

class AuthMiddleware(BaseHTTPMiddleware):
    """JWT 토큰 인증을 위한 미들웨어"""
    
    def __init__(self, app, public_paths=None):
        super().__init__(app)
        # 인증이 필요하지 않은 공개 경로들
        self.public_paths = public_paths or [
            "/",
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/articles/recent",
            "/api/v1/articles/preferred-category",
            "/api/v1/articles/recommend",
            "/api/v1/articles/{article_id}",
        ]
        
        # refresh 토큰만 접근 가능한 경로들
        self.refresh_only_paths = [
            "/api/v1/auth/refresh"
        ]
    
    async def dispatch(self, request: Request, call_next):
        
        # 동적 경로 처리
        is_public_path = request.url.path in self.public_paths
        if not is_public_path:
            # 동적 경로 패턴 매칭
            for pattern in self.public_paths:
                if '{' in pattern:  # 동적 경로 패턴
                    # 패턴을 정규식으로 변환
                    import re
                    regex_pattern = pattern.replace('{', '(?P<').replace('}', '>[^/]+)')
                    if re.match(regex_pattern, request.url.path):
                        is_public_path = True
                        break
        
        is_refresh_only_path = request.url.path in self.refresh_only_paths

        # ✅ Preflight 요청은 인증 없이 통과시킴
        if request.method == "OPTIONS":
            return await call_next(request)
        
        if is_public_path:
            # 공개 경로는 인증 없이 통과
            return await call_next(request)

        # Authorization 헤더 확인
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "): # 토큰이 없으면 401 에러
            return JSONResponse(
                content='{"detail": "Authorization header is required"}',
                status_code=401,
            )
        
        # 토큰 추출
        token = auth_header.split(" ")[1]
        
        # 토큰 검증
        payload = verify_token(token)

        if not payload: # 토큰 검증
            return JSONResponse(
                content='{"detail": "Invalid or expired token"}',
                status_code=401
            )
        
        if is_refresh_only_path:
            if payload.get("type") != "refresh":
                return JSONResponse(
                    content='{"detail": "Invalid token type"}',
                    status_code=401
                )
        else:
            if payload.get("type") != "access":
                return JSONResponse(
                    content='{"detail": "Invalid token type"}',
                    status_code=401
                )
            
        # 요청에 사용자 정보 추가 (User_id 사용)
        user_id = payload.get("User_id")  # User_id에서 UUID 문자열 가져오기
        
        request.state.user_id = user_id
                        
        return await call_next(request) 