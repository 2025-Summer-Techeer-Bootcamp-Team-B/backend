import json
import redis
from typing import List, Optional, Union, Any
from sqlalchemy.orm import Session
from app.models.user_preferred_press import UserPreferredPress
from app.models.user_category import UserCategory
from app.models.user_keyword import UserKeyword
from app.models.press import Press
from app.models.category import Category
from app.models.user import User

# Redis 클라이언트 설정
redis_client = redis.Redis(
    host='redis',
    port=6379,
    db=0,
    decode_responses=True
)

class UserPreferencesCache:
    """사용자 관심 설정 캐싱 서비스"""
    
    CACHE_EXPIRY = 60 * 60 * 24  # 24시간
    
    @staticmethod
    def _get_cache_key(user_id: str, preference_type: str) -> str:
        """캐시 키를 생성합니다."""
        return f"user:{user_id}:preferences:{preference_type}"
    
    @classmethod
    def _get_from_cache(cls, cache_key: str) -> Optional[Any]:
        """캐시에서 데이터를 가져옵니다."""
        cached = redis_client.get(cache_key)
        if cached:
            try:
                return json.loads(cached) if cache_key.endswith(('press', 'category', 'keyword')) else cached
            except Exception:
                pass
        return None
    
    @classmethod
    def _set_cache(cls, cache_key: str, data: Any) -> None:
        """데이터를 캐시에 저장합니다."""
        value = json.dumps(data) if isinstance(data, (list, dict)) else str(data)
        redis_client.setex(cache_key, cls.CACHE_EXPIRY, value)
    
    @classmethod
    def _clear_cache(cls, user_id: str, preference_type: str) -> None:
        """특정 캐시를 삭제합니다."""
        cache_key = cls._get_cache_key(user_id, preference_type)
        redis_client.delete(cache_key)
    
    @classmethod
    def get_user_press(cls, user_id: str, db: Session) -> List[str]:
        """사용자의 관심 언론사를 캐시에서 가져오거나 DB에서 조회"""
        cache_key = cls._get_cache_key(user_id, 'press')
        
        # 캐시에서 조회
        cached = cls._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # DB에서 조회
        press_relations = db.query(UserPreferredPress).filter(
            UserPreferredPress.user_id == user_id
        ).all()
        press_ids = [rel.press_id for rel in press_relations]
        
        press_names = []
        if press_ids:
            presses = db.query(Press).filter(Press.id.in_(press_ids)).all()
            press_names = [press.press_name for press in presses]
        
        # 캐시에 저장
        cls._set_cache(cache_key, press_names)
        return press_names
    
    @classmethod
    def get_user_category(cls, user_id: str, db: Session) -> List[str]:
        """사용자의 관심 카테고리를 캐시에서 가져오거나 DB에서 조회"""
        cache_key = cls._get_cache_key(user_id, 'category')
        
        # 캐시에서 조회
        cached = cls._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # DB에서 조회
        category_relations = db.query(UserCategory).filter(
            UserCategory.user_id == user_id
        ).all()
        category_ids = [rel.category_id for rel in category_relations]
        
        category_names = []
        if category_ids:
            categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
            category_names = [category.category_name for category in categories]
        
        # 캐시에 저장
        cls._set_cache(cache_key, category_names)
        return category_names
    
    @classmethod
    def get_user_keyword(cls, user_id: str, db: Session) -> List[str]:
        """사용자의 관심 키워드를 캐시에서 가져오거나 DB에서 조회"""
        cache_key = cls._get_cache_key(user_id, 'keyword')
        
        # 캐시에서 조회
        cached = cls._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # DB에서 조회
        keywords = db.query(UserKeyword).filter(
            UserKeyword.user_id == user_id
        ).all()
        keyword_list = [kw.keyword for kw in keywords]
        
        # 캐시에 저장
        cls._set_cache(cache_key, keyword_list)
        return keyword_list
    
    @classmethod
    def get_user_voice_type(cls, user_id: str, db: Session) -> str:
        """사용자의 음성 타입을 캐시에서 가져오거나 DB에서 조회"""
        cache_key = cls._get_cache_key(user_id, 'voice_type')
        
        # 캐시에서 조회
        cached = cls._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # DB에서 조회
        user = db.query(User).filter(User.id == user_id).first()
        voice_type = user.voice_type if user else "male"  # 기본값
        
        # 캐시에 저장
        cls._set_cache(cache_key, voice_type)
        return voice_type
    
    @classmethod
    def clear_user_preferences_cache(cls, user_id: str) -> None:
        """사용자의 모든 관심 설정 캐시를 삭제"""
        preference_types = ['press', 'category', 'keyword', 'voice_type']
        for pref_type in preference_types:
            cls._clear_cache(user_id, pref_type)
    
    @classmethod
    def clear_press_cache(cls, user_id: str) -> None:
        """사용자의 관심 언론사 캐시만 삭제"""
        cls._clear_cache(user_id, 'press')
    
    @classmethod
    def clear_category_cache(cls, user_id: str) -> None:
        """사용자의 관심 카테고리 캐시만 삭제"""
        cls._clear_cache(user_id, 'category')
    
    @classmethod
    def clear_keyword_cache(cls, user_id: str) -> None:
        """사용자의 관심 키워드 캐시만 삭제"""
        cls._clear_cache(user_id, 'keyword')
    
    @classmethod
    def clear_voice_type_cache(cls, user_id: str) -> None:
        """사용자의 음성 타입 캐시만 삭제"""
        cls._clear_cache(user_id, 'voice_type') 