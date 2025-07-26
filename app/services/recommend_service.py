from typing import List
from opensearchpy import OpenSearch
import openai
import os
from dotenv import load_dotenv
from app.core.database import SessionLocal
from app.models.user_keyword import UserKeyword
from app.models.news_article import NewsArticle
import logging
from openai import AsyncOpenAI
import asyncio

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

client_os = OpenSearch(
    hosts=[{'host': 'opensearch', 'port': 9200}],
    http_auth=('admin', 'admin'),
    use_ssl=False,
)

#인덱스 생성
def create_news_index():
    index_body = {
        "settings": {
            "index": {
                "knn": True
            }
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


#인덱스에 임베딩된 제목과 요약문 저장
async def index_article(article_id, title, content):
    embedding = await get_embedding_async(f"{title} {content}")
    doc = {
        "title": title,
        "content": content,
        "embedding": embedding
    }
    # OpenSearch 인덱싱은 동기 클라이언트이므로 await 불가 (병목 가능성 있음)
    client_os.index(index="news-articles", id=article_id, body=doc)

#뉴스 기사 테이블을 모두 비동기로 인덱싱
async def index_all_articles(db):
    articles = db.query(NewsArticle).filter_by(is_deleted=False).all()
    # 각 기사에 대해 index_article 코루틴 생성
    tasks = [index_article(str(article.id), article.title, article.summary_text) for article in articles]
    # 모든 태스크를 병렬로 실행
    await asyncio.gather(*tasks)

#유저 관심사 키워드 가져오기
def get_user_keywords(user_id: str, db) -> List[str]:
    keywords = db.query(UserKeyword).filter_by(user_id=user_id, is_deleted=False).all()
    logging.info(keywords)
    return [kw.keyword for kw in keywords]

#문자열 임베딩 (비동기)
async def get_embedding_async(text: str) -> list:
    response = await async_client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

#임베딩된 키워드로 기사 찾기 (동기)
def search_similar_articles_by_embedding(embedding, top_k=10):
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
    response = client_os.search(index="news-articles", body=query)
    return response['hits']['hits']

#유저별 추천 기사 (비동기)
async def recommend_articles_for_user_async(user_id: str, db, top_k=30):
    keywords = get_user_keywords(user_id, db)
    results = []
    seen_ids = set()
    # 여러 키워드 임베딩을 병렬로 요청
    embeddings = await asyncio.gather(*(get_embedding_async(keyword) for keyword in keywords))
    for embedding in embeddings:
        articles = search_similar_articles_by_embedding(embedding, top_k=30)
        for hit in articles:
            article_id = hit["_id"]
            if article_id not in seen_ids:
                seen_ids.add(article_id)
                source = hit["_source"]
                results.append({
                    "id": article_id,
                    "title": source.get("title", ""),
                    "content": source.get("content", ""),
                    "score": hit["_score"]
                })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k] 