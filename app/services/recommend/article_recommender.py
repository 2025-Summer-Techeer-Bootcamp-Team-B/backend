import asyncio
from app.models.news_article import NewsArticle
from app.services.recommend.opensearch import bulk_index_articles, search_similar_articles_by_embedding_async
from app.services.recommend.redis_cache import get_or_cache_keyword_embedding
from app.services.recommend.user_keywords import get_user_keywords
from app.core.query import get_user_preferred_articles

# 사용자의 선호 언론사/카테고리 기사만 비동기 bulk 인덱싱
async def index_user_preferred_articles(db, user_id: str):
    """사용자의 선호 기사들을 인덱싱합니다."""
    articles = get_user_preferred_articles(db, user_id)
    if articles:
        await bulk_index_articles(articles)

# 유저별 추천 기사 (비동기)
async def recommend_articles_for_user_async(db, user_id, top_k=30):
    """사용자별 추천 기사를 생성합니다."""
    keywords = get_user_keywords(db, user_id)
    print(f"🔍 사용자 {user_id}의 키워드: {keywords}")
    
    if not keywords:
        print("❌ 사용자 키워드가 없습니다.")
        return []
    
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
                
                if article and hit["_score"] >= 0.6:  # 스코어 임계값을 0.6으로 조정
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
    print(f"🎯 추천 기사 결과: {len(results)}개")
    return results[:top_k]

# 특정 키워드별 추천 기사 (비동기)
async def recommend_articles_by_keyword_async(db, user_id, keyword, top_k=10):
    """특정 키워드로 추천 기사를 생성합니다."""
    print(f"🔍 사용자 {user_id}의 키워드 '{keyword}'로 추천 기사 생성")
    
    # 키워드 임베딩 가져오기
    embedding = await get_or_cache_keyword_embedding(user_id, keyword)
    
    # 유사한 기사 검색
    articles = await search_similar_articles_by_embedding_async(embedding, top_k=20)
    
    results = []
    for hit in articles:
        article_id = hit["_id"]
        # 데이터베이스에서 실제 기사 정보 가져오기
        article = db.query(NewsArticle).filter(
            NewsArticle.id == article_id,
            NewsArticle.is_deleted == False
        ).first()
        
        if article and hit["_score"] >= 0.6:  # 스코어 임계값을 0.6으로 조정
            # 키워드가 제목이나 내용에 포함되어 있는지 확인 (우선순위 부여)
            title_contains_keyword = keyword.lower() in article.title.lower()
            content_contains_keyword = keyword.lower() in article.summary_text.lower() if article.summary_text else False
            
            # 키워드가 포함된 기사에 더 높은 스코어 부여
            adjusted_score = hit["_score"]
            if title_contains_keyword:
                adjusted_score += 0.3
            elif content_contains_keyword:
                adjusted_score += 0.1
            
            results.append({
                "id": str(article.id),
                "title": article.title,
                "content": article.summary_text,
                "thumbnail_image_url": article.thumbnail_image_url,
                "category_name": article.category_name,
                "author": article.author,
                "published_at": article.published_at,
                "score": adjusted_score,
                "keyword": keyword
            })
    
    # 스코어 순으로 정렬
    results.sort(key=lambda x: x["score"], reverse=True)
    print(f"🎯 키워드 '{keyword}' 추천 기사 결과: {len(results)}개")
    return results[:top_k]

 