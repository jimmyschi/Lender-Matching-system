"""
Database connection and session management using SQLAlchemy.

Uses synchronous SQLAlchemy with a connection pool sized for a single-process
FastAPI server. The session factory is exposed via get_db(), which yields one
session per request and rolls back automatically on unhandled exceptions.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://kaaj:kaaj@localhost:5432/kaaj")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
