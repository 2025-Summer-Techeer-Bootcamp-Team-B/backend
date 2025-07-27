import os
import json
import aiohttp
from typing import List
from opensearchpy import OpenSearch
from app.models.news_article import NewsArticle
from app.services.recommend.text_embedding import get_embeddings_batch_async

client_os = OpenSearch(
    hosts=[{'host': 'opensearch', 'port': 9200}],
    http_auth=('admin', 'admin'),
    use_ssl=False,
)

def create_news_index():
    """뉴스 기사 인덱스를 생성합니다."""
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

async def bulk_index_articles(articles: List[NewsArticle]):
    """OpenSearch /_bulk API로 여러 기사를 한 번에 인덱싱합니다."""
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

OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://opensearch:9200")

async def search_similar_articles_by_embedding_async(embedding, top_k=10):
    """임베딩된 키워드로 유사한 기사를 찾습니다 (비동기, aiohttp)."""
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