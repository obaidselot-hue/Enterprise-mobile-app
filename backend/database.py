import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings

logger = logging.getLogger("uvicorn.info")

db_url = settings.EFFECTIVE_DATABASE_URL
is_sqlite = db_url.startswith("sqlite")

connect_args = {"check_same_thread": False} if is_sqlite else {}
pool_kwargs = {} if is_sqlite else {"pool_pre_ping": True, "pool_size": 10, "max_overflow": 20}

engine = create_engine(db_url, connect_args=connect_args, **pool_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """FastAPI dependency that yields an isolated DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
