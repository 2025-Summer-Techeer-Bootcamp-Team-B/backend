import os
import json
import asyncio
import logging
from typing import List
from dotenv import load_dotenv
from opensearchpy import OpenSearch
from openai import AsyncOpenAI
import aiohttp
from app.core.database import SessionLocal
from app.models.user_keyword import UserKeyword
from app.models.news_article import NewsArticle
from app.services.article_service.query import get_user_preferred_articles
import redis

load_dotenv()

async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=int(os.getenv("REDIS_PORT", 6379)), db=int(os.getenv("REDIS_DB", 0)), decode_responses=True)

client_os = OpenSearch(
    hosts=[{'host': 'opensearch', 'port': 9200}],
    http_auth=('admin', 'admin'),
    use_ssl=False,
)

# 인덱스 생성
def create_news_index():
    index_body = {
        "settings": {
            "index": {"knn": True}
        },
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "content": {"type": "text"},
                "embedding": {"type": "knn_vector", "dimension": 1536}
            }
        }
    }
    client_os.indices.create(index="news-articles", body=index_body, ignore=400)

async def get_embedding_async(text: str) -> list:
    response = await async_client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

async def get_embeddings_batch_async(texts: List[str]) -> List[List[float]]:
    try:
        response = await async_client.embeddings.create(
            input=texts,
            model="text-embedding-ada-002"
        )
        return [r.embedding for r in response.data]
    except Exception as e:
        logging.error(f"❌ Embedding batch 실패: {e}")
        raise

# 비동기 임베딩 (세마포어 적용)
async def get_embedding_async_limited(text: str, semaphore: asyncio.Semaphore) -> list:
    async with semaphore:
        return await get_embedding_async(text)

# OpenSearch /_bulk API로 한 번에 인덱싱
async def bulk_index_articles(articles: List[NewsArticle]):
    texts = [f"{article.title} {article.summary_text}" for article in articles]
    article_ids = [str(article.id) for article in articles]
    titles = [article.title for article in articles]
    contents = [article.summary_text for article in articles]

    embeddings = await get_embeddings_batch_async(texts)  # ✅ 한 번에 전체 처리

    bulk_lines = []
    for article_id, title, content, embedding in zip(article_ids, titles, contents, embeddings):
        action = {"index": {"_index": "news-articles", "_id": article_id}}
        doc = {"title": title, "content": content, "embedding": embedding}
        bulk_lines.append(json.dumps(action))
        bulk_lines.append(json.dumps(doc))

    bulk_body = "\n".join(bulk_lines) + "\n"
    opensearch_url = "http://opensearch:9200/_bulk"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            opensearch_url,
            data=bulk_body,
            headers={"Content-Type": "application/x-ndjson"},
            auth=aiohttp.BasicAuth("admin", "admin")
        ) as resp:
            result = await resp.json()
            if not result.get("errors"):
                print(f"✅ Bulk 인덱싱 성공 ({len(articles)}개)")
            else:
                print(f"❌ Bulk 인덱싱 에러: {result}")
            return result

# 사용자의 선호 언론사/카테고리 기사만 비동기 bulk 인덱싱
async def index_user_preferred_articles(db, user_id: str):
    articles = get_user_preferred_articles(db, user_id)
    if articles:
        await bulk_index_articles(articles)

# 유저 관심사 키워드 가져오기
def get_user_keywords(db, user_id) -> List[str]:
    keywords = db.query(UserKeyword).filter_by(user_id=user_id, is_deleted=False).all()
    logging.info(keywords)
    return [kw.keyword for kw in keywords]

OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://opensearch:9200")

# 임베딩된 키워드로 기사 찾기 (비동기, aiohttp)
async def search_similar_articles_by_embedding_async(embedding, top_k=10):
    query = {
        "size": top_k,
        "query": {
            "knn": {
                "embedding": {
                    "vector": embedding,
                    "k": top_k
                }
            }
        }
    }
    url = f"{OPENSEARCH_URL}/news-articles/_search"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            json=query,
            auth=aiohttp.BasicAuth("admin", "admin"),
            headers={"Content-Type": "application/json"}
        ) as resp:
            result = await resp.json()
            return result['hits']['hits']

# 키워드 임베딩 캐싱 함수
async def get_or_cache_keyword_embedding(user_id: str, keyword: str) -> list:
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

# 유저별 추천 기사 (비동기)
async def recommend_articles_for_user_async(db, user_id, top_k=30):
    keywords = get_user_keywords(db, user_id)
    results = []
    seen_ids = set()
    semaphore = asyncio.Semaphore(10)
    embeddings = await asyncio.gather(*(get_or_cache_keyword_embedding(user_id, keyword) for keyword in keywords))
    for embedding in embeddings:
        articles = await search_similar_articles_by_embedding_async(embedding, top_k=30)
        for hit in articles:
            article_id = hit["_id"]
            if article_id not in seen_ids:
                seen_ids.add(article_id)
                # 데이터베이스에서 실제 기사 정보 가져오기
                article = db.query(NewsArticle).filter(
                    NewsArticle.id == article_id,
                    NewsArticle.is_deleted == False
                ).first()
                
                if article and hit["_score"] >= 0.75:  # 스코어 0.75 이상만 필터링
                    results.append({
                        "id": str(article.id),
                        "title": article.title,
                        "content": article.summary_text,
                        "thumbnail_image_url": article.thumbnail_image_url,
                        "category_name": article.category_name,
                        "author": article.author,
                        "published_at": article.published_at,
                        "score": hit["_score"]
                    })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k] 