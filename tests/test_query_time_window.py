import datetime

from app.core import query
from app.models import Category, NewsArticle, Press, User, UserCategory, UserPreferredPress

KST = datetime.timezone(datetime.timedelta(hours=9))


def _seed_article_published_after_server_start(db, published_at):
    user = User(email="reader@example.com", password="hashed", refresh_token="None")
    press = Press(press_name="한국경제")
    category = Category(category_name="경제")
    db.add_all([user, press, category])
    db.flush()
    db.add_all([
        UserPreferredPress(user_id=user.id, press_id=press.id),
        UserCategory(user_id=user.id, category_id=category.id),
        NewsArticle(
            title="서버 기동 이후 발행된 기사",
            url="https://example.com/news/1",
            published_at=published_at,
            summary_text="요약",
            male_audio_url="https://storage.example.com/male.mp3",
            female_audio_url="https://storage.example.com/female.mp3",
            thumbnail_image_url="https://storage.example.com/thumb.jpg",
            author="기자",
            category_name="경제",
            press_id=press.id,
            category_id=category.id,
        ),
    ])
    db.commit()
    return user


def _clock_two_hours_after_server_start(monkeypatch):
    # 서버가 뜬 뒤 2시간이 지난 시점의 "최근 12시간" 범위
    now = datetime.datetime.now(KST) + datetime.timedelta(hours=2)
    monkeypatch.setattr(query, "get_today_range_kst", lambda: (now - datetime.timedelta(hours=12), now))
    return now


def test_preferred_category_includes_article_published_after_server_start(db, monkeypatch):
    now = _clock_two_hours_after_server_start(monkeypatch)
    user = _seed_article_published_after_server_start(db, published_at=now - datetime.timedelta(hours=1))

    articles = query.get_articles_by_category_and_user_press(db, user.id, "경제")

    assert [a.title for a in articles] == ["서버 기동 이후 발행된 기사"]


def test_recommend_candidates_include_article_published_after_server_start(db, monkeypatch):
    now = _clock_two_hours_after_server_start(monkeypatch)
    user = _seed_article_published_after_server_start(db, published_at=now - datetime.timedelta(hours=1))

    articles = query.get_user_preferred_articles(db, user.id)

    assert [a.title for a in articles] == ["서버 기동 이후 발행된 기사"]
