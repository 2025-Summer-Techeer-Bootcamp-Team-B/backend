from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user_setting import UserSetting, UserHistory, UserHistoryItem
from app.models.user import User
from app.models.user_category import UserCategory
from app.models.article_history import ArticleHistory
from app.models.news_article import NewsArticle
from app.models.category import Category
from app.models.press import Press
from app.models.user_preferred_press import UserPreferredPress
from app.models.user_keyword import UserKeyword
from app.services.user_setting import get_user, get_user_history

router = APIRouter(prefix="/user", tags=["user"])

#user_id 가져오기
def get_user_id_from_request(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    return user_id

# 관계 지우기
def clear_user_relations(db: Session, model, user_id: str):
    db.query(model).filter(model.user_id == user_id).delete()
    db.commit()

# 선택된 이름 가져오기
def get_selected_names(db: Session, user, relation_attr: str, model, name_field: str, id_field: str):
    ids = [getattr(rel, id_field) for rel in getattr(user, relation_attr)]
    if not ids:
        return []
    objs = db.query(model).filter(getattr(model, 'id').in_(ids)).all()
    return [getattr(obj, name_field) for obj in objs]

# 언론사 설정
@router.put("/press", response_model=UserSetting)
def user_press_setting(request: Request, user_setting: UserSetting, db: Session = Depends(get_db)):
    user_id = get_user_id_from_request(request)
    user = get_user(user_id, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user_setting.press is None:
        raise HTTPException(status_code=400, detail="Press is required")
    clear_user_relations(db, UserPreferredPress, user_id)
    for press_name in user_setting.press:
        press = db.query(Press).filter(Press.press_name == press_name).first()
        if press:
            db.add(UserPreferredPress(user_id=user_id, press_id=press.id))
    db.commit()
    db.refresh(user)
    selected_press_names = get_selected_names(db, user, 'preferred_presses', Press, 'press_name', 'press_id')
    return UserSetting(press=selected_press_names)

# 카테고리 설정
@router.put("/category", response_model=UserSetting)
def user_category_setting(request: Request, user_setting: UserSetting, db: Session = Depends(get_db)):
    user_id = get_user_id_from_request(request)
    user = get_user(user_id, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user_setting.category is None:
        raise HTTPException(status_code=400, detail="Category is required")
    clear_user_relations(db, UserCategory, user_id)
    for category_name in user_setting.category:
        category = db.query(Category).filter(Category.category_name == category_name).first()
        if category:
            db.add(UserCategory(user_id=user_id, category_id=category.id))
    db.commit()
    db.refresh(user)
    selected_category_names = get_selected_names(db, user, 'user_categories', Category, 'category_name', 'category_id')
    return UserSetting(category=selected_category_names)

# 키워드 설정
@router.put("/keyword", response_model=UserSetting)
def user_keyword_setting(request: Request, user_setting: UserSetting, db: Session = Depends(get_db)):
    user_id = get_user_id_from_request(request)
    user = get_user(user_id, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user_setting.keyword is None:
        raise HTTPException(status_code=400, detail="Keyword is required")
    clear_user_relations(db, UserKeyword, user_id)
    for keyword in user_setting.keyword:
        db.add(UserKeyword(user_id=user_id, keyword=keyword))
    db.commit()
    db.refresh(user)
    selected_keywords = [kw.keyword for kw in user.keywords]
    return UserSetting(keyword=selected_keywords)

# 조회 기록 가져오기
@router.get("/history", response_model=UserHistory)
def user_history(request: Request, db: Session = Depends(get_db)):
    user_id = get_user_id_from_request(request)
    user = get_user(user_id, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    histories = get_user_history(user_id, db)
    user_history = []
    for history in histories:
        article = history.article
        if history.news_id is None:
            raise HTTPException(status_code=404, detail="News not found")
        if article.thumbnail_image_url is None:
            raise HTTPException(status_code=404, detail="Thumbnail image not found")
        if article.url is None:
            raise HTTPException(status_code=404, detail="URL not found")
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