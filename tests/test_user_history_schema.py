import datetime
import uuid

from app.schemas.user_setting import UserHistory


def test_user_history_accepts_values_built_by_history_router():
    # app/routers/user.py 의 user_history() 가 만드는 값 그대로: ORM 의 UUID 와 datetime
    user_id = uuid.uuid4()
    news_id = uuid.uuid4()
    viewed_at = datetime.datetime(2025, 7, 30, 8, 15, 0)

    history = UserHistory(histories=[{
        "user_id": user_id,
        "news_id": news_id,
        "title": "기사 제목",
        "thumbnail_image_url": "https://storage.example.com/thumb.jpg",
        "url": "https://example.com/news/1",
        "category": "경제",
        "viewed_at": viewed_at,
    }])

    item = history.model_dump(mode="json")["histories"][0]
    assert item["user_id"] == str(user_id)
    assert item["news_id"] == str(news_id)
    assert item["viewed_at"] == "2025-07-30T08:15:00"
