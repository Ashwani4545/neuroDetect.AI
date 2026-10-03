from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from app.config import DATABASE_URL

if DATABASE_URL.startswith('sqlite'):
    connect_args = {'check_same_thread': False}
    # An in-memory sqlite DB is connection-scoped: without StaticPool, each
    # new connection (e.g. from a fresh request) gets its OWN empty database.
    # Used by the test suite (DATABASE_URL=sqlite:///:memory:).
    poolclass = StaticPool if ':memory:' in DATABASE_URL else None
    engine = create_engine(DATABASE_URL, connect_args=connect_args, poolclass=poolclass) \
        if poolclass else create_engine(DATABASE_URL, connect_args=connect_args)
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app import models_db  # noqa: F401 — ensure models are registered before create_all
    Base.metadata.create_all(bind=engine)
