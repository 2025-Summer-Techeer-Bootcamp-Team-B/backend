from sqlalchemy.orm import Session
from app.models.user import User
from app.services.auth.password_utils import hash_password, verify_password
import datetime

def create_user(db: Session, request_user_email: str, request_user_password: str):
    hashed_password = hash_password(request_user_password)
    new_user = User(
        email=request_user_email,
        password=hashed_password,
        voice_type="None",
        refresh_token="None",
        created_at=datetime.datetime.utcnow(),
        is_deleted=False,
    )
    db.add(new_user)
    db.commit()
    return new_user

def get_user_by_email(db: Session, request_user_email: str): # 이메일로 유저 조회
    return db.query(User).filter(User.email == request_user_email).first()

def login_process(db: Session, request_user_email: str, request_user_password: str): # 로그인 처리
    user = db.query(User).filter(User.email == request_user_email).first()
    if user is None:
        return False
    if verify_password(request_user_password, user.password):
        return user
    else:
        return False