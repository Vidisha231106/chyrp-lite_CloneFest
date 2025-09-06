# database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Use Supabase PostgreSQL database URL
DATABASE_URL = os.getenv("SUPABASE_DATABASE_URL")

# Fallback to local SQLite if Supabase URL not provided
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./blog.db"

# Create engine with connection pooling for better performance
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()