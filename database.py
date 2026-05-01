from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/SnapLink"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# This is your URLs table
class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, nullable=False)
    short_code = Column(String, unique=True, index=True)
    click_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

# Creates the table in PostgreSQL
Base.metadata.create_all(bind=engine)

# Dependency — gives us a DB session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()