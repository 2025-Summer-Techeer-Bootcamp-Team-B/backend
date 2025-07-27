import os
import json
import redis
from typing import List
from dotenv import load_dotenv
from app.services.recommend.text_embedding import get_embedding_async

load_dotenv()

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"), 
    port=int(os.getenv("REDIS_PORT", 6379)), 
    db=int(os.getenv("REDIS_DB", 0)), 
    decode_responses=True
)

async def get_or_cache_keyword_embedding(user_id: str, keyword: str) -> List[float]:
    """키워드 임베딩을 캐싱하거나 가져옵니다."""
    cache_key = f"user:{user_id}:keyword_embedding:{keyword}"
    cached = redis_client.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass
    embedding = await get_embedding_async(keyword)
    redis_client.setex(cache_key, 60 * 60 * 24, json.dumps(embedding))  # 24시간 캐싱
    return embedding 