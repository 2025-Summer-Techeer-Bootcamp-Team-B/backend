from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user_setting import UserSetting, UserHistory
from app.models.user_category import UserCategory
from app.models.category import Category
from app.models.press import Press
from app.models.user_preferred_press import UserPreferredPress
from app.models.user_keyword import UserKeyword
from app.models.user import User
from app.services.users import get_user_history, UserPreferencesCache

router = APIRouter(prefix="/user", tags=["user"])

def get_current_user(request: Request, db: Session) -> User:
    """현재 인증된 사용자를 가져옵니다."""
    user_id = request.state.user_id
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def clear_user_relations(db: Session, model, user_id: str):
    """사용자의 특정 관계 데이터를 삭제합니다."""
    db.query(model).filter(model.user_id == user_id).delete()
    db.commit()

def get_selected_names(db: Session, user, relation_attr: str, model, name_field: str, id_field: str):
    """관계 테이블에서 선택된 이름들을 가져옵니다."""
    ids = [getattr(rel, id_field) for rel in getattr(user, relation_attr)]
    if not ids:
        return []
    objs = db.query(model).filter(getattr(model, 'id').in_(ids)).all()
    return [getattr(obj, name_field) for obj in objs]

# ==================== GET 엔드포인트들 ====================

@router.get("/press", response_model=UserSetting)
def get_user_press(request: Request, db: Session = Depends(get_db)):
    """사용자의 관심 언론사를 조회합니다."""
    user = get_current_user(request, db)
    press_names = UserPreferencesCache.get_user_press(user.id, db)
    return UserSetting(press=press_names)

@router.get("/category", response_model=UserSetting)
def get_user_category(request: Request, db: Session = Depends(get_db)):
    """사용자의 관심 카테고리를 조회합니다."""
    user = get_current_user(request, db)
    category_names = UserPreferencesCache.get_user_category(user.id, db)
    return UserSetting(category=category_names)

@router.get("/keyword", response_model=UserSetting)
def get_user_keyword(request: Request, db: Session = Depends(get_db)):
    """사용자의 관심 키워드를 조회합니다."""
    user = get_current_user(request, db)
    keyword_list = UserPreferencesCache.get_user_keyword(user.id, db)
    return UserSetting(keyword=keyword_list)

@router.get("/voice-type", response_model=UserSetting)
def get_user_voice_type(request: Request, db: Session = Depends(get_db)):
    """사용자의 음성 타입을 조회합니다."""
    user = get_current_user(request, db)
    voice_type = UserPreferencesCache.get_user_voice_type(user.id, db)
    return UserSetting(voice_type=voice_type)

@router.get("/history", response_model=UserHistory)
def user_history(request: Request, db: Session = Depends(get_db)):
    """사용자의 조회 기록을 가져옵니다."""
    user = get_current_user(request, db)
    histories = get_user_history(user.id, db)
    
    user_history = []
    for history in histories:
        article = history.article
        if not all([history.news_id, article.thumbnail_image_url, article.url]):
            continue  # 필수 필드가 없는 경우 건너뛰기
        
        user_history.append({
            "user_id": user.id,
            "news_id": history.news_id,
            "title": article.title,
            "thumbnail_image_url": article.thumbnail_image_url,
            "url": article.url,
            "category": article.category.category_name,
            "viewed_at": history.viewed_at
        })
    
    return UserHistory(histories=user_history)

# ==================== PUT 엔드포인트들 ====================

@router.put("/press", response_model=UserSetting)
def user_press_setting(request: Request, user_setting: UserSetting, db: Session = Depends(get_db)):
    """사용자의 관심 언론사를 설정합니다."""
    user = get_current_user(request, db)
    
    if user_setting.press is None:
        raise HTTPException(status_code=400, detail="Press is required")
    
    # 기존 관계 삭제
    clear_user_relations(db, UserPreferredPress, user.id)
    
    # 새로운 관계 추가
    for press_name in user_setting.press:
        press = db.query(Press).filter(Press.press_name == press_name).first()
        if press:
            db.add(UserPreferredPress(user_id=user.id, press_id=press.id))
    
    db.commit()
    db.refresh(user)
    
    # 캐시 삭제
    UserPreferencesCache.clear_press_cache(user.id)
    
    # 설정된 언론사 이름들 반환
    selected_press_names = get_selected_names(db, user, 'preferred_presses', Press, 'press_name', 'press_id')
    return UserSetting(press=selected_press_names)

@router.put("/category", response_model=UserSetting)
def user_category_setting(request: Request, user_setting: UserSetting, db: Session = Depends(get_db)):
    """사용자의 관심 카테고리를 설정합니다."""
    user = get_current_user(request, db)
    
    if user_setting.category is None:
        raise HTTPException(status_code=400, detail="Category is required")
    
    # 기존 관계 삭제
    clear_user_relations(db, UserCategory, user.id)
    
    # 새로운 관계 추가
    for category_name in user_setting.category:
        category = db.query(Category).filter(Category.category_name == category_name).first()
        if category:
            db.add(UserCategory(user_id=user.id, category_id=category.id))
    
    db.commit()
    db.refresh(user)
    
    # 캐시 삭제
    UserPreferencesCache.clear_category_cache(user.id)
    
    # 설정된 카테고리 이름들 반환
    selected_category_names = get_selected_names(db, user, 'user_categories', Category, 'category_name', 'category_id')
    return UserSetting(category=selected_category_names)

@router.put("/keyword", response_model=UserSetting)
def user_keyword_setting(request: Request, user_setting: UserSetting, db: Session = Depends(get_db)):
    """사용자의 관심 키워드를 설정합니다."""
    user = get_current_user(request, db)
    
    if user_setting.keyword is None:
        raise HTTPException(status_code=400, detail="Keyword is required")
    
    # 기존 관계 삭제
    clear_user_relations(db, UserKeyword, user.id)
    
    # 새로운 관계 추가
    for keyword in user_setting.keyword:
        db.add(UserKeyword(user_id=user.id, keyword=keyword))
    
    db.commit()
    db.refresh(user)
    
    # 캐시 삭제
    UserPreferencesCache.clear_keyword_cache(user.id)
    
    # 설정된 키워드들 반환
    selected_keywords = [kw.keyword for kw in user.keywords]
    return UserSetting(keyword=selected_keywords)

@router.put("/voice-type", response_model=UserSetting)
def user_voice_type_setting(request: Request, voice_setting: UserSetting, db: Session = Depends(get_db)):
    """사용자의 음성 타입을 설정합니다."""
    user = get_current_user(request, db)
    
    if voice_setting.voice_type is None:
        raise HTTPException(status_code=400, detail="Voice type is required")
    
    # voice_type 유효성 검사
    if voice_setting.voice_type not in ["male", "female"]:
        raise HTTPException(status_code=400, detail="Voice type must be 'male' or 'female'")
    
    # voice_type 업데이트
    user.voice_type = voice_setting.voice_type
    db.commit()
    db.refresh(user)
    
    # 캐시 삭제
    UserPreferencesCache.clear_voice_type_cache(user.id)
    
    return UserSetting(voice_type=user.voice_type)

