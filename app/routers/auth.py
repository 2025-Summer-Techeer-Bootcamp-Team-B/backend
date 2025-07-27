from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.users.user_service import create_user, get_user_by_email, login_process
from app.models.user import User
from app.services.auth.jwt_utils import create_access_token, create_refresh_token, verify_token
from app.schemas.user import (
    UserBase, RegisterResponse, LoginResponse, RefreshRequest, EmailExistsResponse
)
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=RegisterResponse)
def register_user(user_data: UserBase, db: Session = Depends(get_db)):
    # 입력 검증
    if not user_data.email or user_data.email.strip() == "":
        raise HTTPException(status_code=400, detail="이메일은 비어있을 수 없습니다.")
    
    if not user_data.password or user_data.password.strip() == "":
        raise HTTPException(status_code=400, detail="비밀번호는 비어있을 수 없습니다.")
    
    if len(user_data.password) < 6:
        raise HTTPException(status_code=400, detail="비밀번호는 최소 6자 이상이어야 합니다.")
    
    # 이메일 형식 검증
    if "@" not in user_data.email or "." not in user_data.email:
        raise HTTPException(status_code=400, detail="올바른 이메일 형식이 아닙니다.")
    
    request_user = get_user_by_email(db, user_data.email)

    if request_user is None:
        user = create_user(db, user_data.email, user_data.password)
        
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        
        user.refresh_token = refresh_token
        db.commit()
        
        return RegisterResponse(
            message="회원가입이 완료되었습니다.", 
            email=user_data.email,
            access_token=access_token,
            refresh_token=refresh_token
        )
    else:
        raise HTTPException(status_code=409, detail="이미 존재하는 이메일입니다.")
    
@router.get("/exists", response_model=EmailExistsResponse)
def check_email_exists(email: str, db: Session = Depends(get_db)):
    user = get_user_by_email(db, email)
    if user is None:
        raise HTTPException(status_code=404, detail="이메일이 존재하지 않습니다.")
    else:
        return EmailExistsResponse(exists=True, email=email)    

@router.post("/login", response_model=LoginResponse)
def login_user(user_data: UserBase, response: Response, db: Session = Depends(get_db)):
    # 입력 검증
    if not user_data.email or user_data.email.strip() == "":
        raise HTTPException(status_code=400, detail="이메일은 비어있을 수 없습니다.")
    
    if not user_data.password or user_data.password.strip() == "":
        raise HTTPException(status_code=400, detail="비밀번호는 비어있을 수 없습니다.")
    
    user = login_process(db, user_data.email, user_data.password)
    if user is False:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    
    refresh_token = create_refresh_token(user.id)
    access_token = create_access_token(user.id)
    
    user.refresh_token = refresh_token
    db.commit()

    return LoginResponse(
        message="로그인이 완료되었습니다.",
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/refresh", response_model=RegisterResponse)
async def refresh_token(token_data: RefreshRequest, response: Response, db: Session = Depends(get_db)):
    # 입력 검증
    if not token_data.refresh_token or token_data.refresh_token.strip() == "":
        raise HTTPException(status_code=400, detail="리프레시 토큰은 비어있을 수 없습니다.")
    
    payload = verify_token(token_data.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="유효하지 않은 리프레시 토큰입니다.")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="잘못된 토큰 타입입니다.")
    user_id = payload.get("User_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
   
    new_access_token = create_access_token(user.id)

    return RegisterResponse(
        message="토큰이 성공적으로 갱신되었습니다",
        email=user.email,
        access_token=new_access_token,
        refresh_token=token_data.refresh_token
    )

# 미들웨어 테스트용 엔드포인트
@router.get("/test-middleware")
async def test_middleware(request: Request):
    """미들웨어가 제대로 작동하는지 테스트하는 엔드포인트"""
    # request.state에서 미들웨어가 설정한 정보 확인
    user_id = getattr(request.state, 'user_id', None)
    
    return {
        "message": "미들웨어 테스트 성공!",
        "user_id_from_middleware": user_id,
    }