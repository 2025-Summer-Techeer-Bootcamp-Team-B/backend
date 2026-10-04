import datetime
import sys
import types

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# app.core.database 는 import 시점에 PostgreSQL 접속(최대 10회 재시도)을 하고,
# app.core.save 는 celery_app -> GCS 클라이언트 생성까지 연쇄 import 한다.
# 테스트에서는 이 두 모듈만 가벼운 대체 모듈로 바꾸고, 쿼리는 실제 SQLite 에서 실행한다.
_database = types.ModuleType("app.core.database")
_database.Base = declarative_base()
_database.get_db = None
sys.modules["app.core.database"] = _database

_save = types.ModuleType("app.core.save")
_save.KST = datetime.timezone(datetime.timedelta(hours=9))
sys.modules["app.core.save"] = _save

import app.models  # noqa: E402,F401  모델을 Base.metadata 에 등록


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    _database.Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
