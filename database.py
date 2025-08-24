from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ Переменная окружения DATABASE_URL не найдена. Проверь файл .env")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Проверяет соединение перед использованием
    pool_recycle=3600,       # Перезапускает соединение каждые 60 мин
    echo=False,              # Включить True для логов SQL-запросов
    future=True              # Поддержка SQLAlchemy 2.x
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
