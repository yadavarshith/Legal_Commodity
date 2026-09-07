import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Defaults to the in-container Postgres (see docker-compose.yml).
# Override with DATABASE_URL for local dev, e.g. sqlite:///./labelsure.db
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://labelsure:labelsure_dev@db:5432/labelsure")

_connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    from .models import InspectionCase, InspectorDecision
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
