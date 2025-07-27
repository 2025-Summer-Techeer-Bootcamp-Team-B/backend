from typing import List
from app.models.user_keyword import UserKeyword

def get_user_keywords(db, user_id) -> List[str]:
    """사용자의 관심 키워드 목록을 가져옵니다."""
    keywords = db.query(UserKeyword).filter_by(user_id=user_id, is_deleted=False).all()
    return [kw.keyword for kw in keywords] 