from typing import List
from opensearchpy import OpenSearch
import openai
import os
from dotenv import load_dotenv
from app.core.database import SessionLocal
from app.models.user_keyword import UserKeyword
from app.models.news_article import NewsArticle
import logging

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
def index_article(article_id, title, content):
    embedding = get_embedding(f"{title} {content}")
    doc = {
        "title": title,
        "content": content,
        "embedding": embedding
    }
    client_os.index(index="news-articles", id=article_id, body=doc)

#뉴스 기사 테이블을 모두 불러오기
def index_all_articles(db):
    articles = db.query(NewsArticle).filter_by(is_deleted=False).all()
    for article in articles:
        index_article(
            str(article.id),
            article.title,
            article.summary_text  # 또는 article.content 등
        )

#유저 관심사 키워드 가져오기
def get_user_keywords(user_id: str, db) -> List[str]:
    keywords = db.query(UserKeyword).filter_by(user_id=user_id, is_deleted=False).all()
    logging.info(keywords)
    return [kw.keyword for kw in keywords]

#문자열 임베딩
def get_embedding(text: str) -> list:
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

#임베딩된 키워드로 기사 찾기
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

#메인 메서드
def recommend_articles_for_user(user_id: str, db, top_k=10):
    keywords = get_user_keywords(user_id, db)
    results = []
    seen_ids = set()
    for keyword in keywords:
        embedding = get_embedding(keyword)
        articles = search_similar_articles_by_embedding(embedding, top_k=5)
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