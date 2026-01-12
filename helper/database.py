import os
import dotenv
from urllib.parse import quote_plus
from sqlalchemy import text
from typing import AsyncGenerator

from utils.log_debug import log_debug

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

env = os.getenv("APP_ENV", "local")
dotenv.load_dotenv(f".env.{env}")

DB_HOST = os.getenv("PGSQL_HOST", "localhost")
DB_USER = os.getenv("PGSQL_USER", "postgres")
DB_PORT = os.getenv("PGSQL_PORT", "5432")
DB_DATABASE = os.getenv("PGSQL_DATABASE", "posts_monitoring")
DB_PASSWORD = os.getenv("PGSQL_PASSWORD", "")

# ---------------------------------------------------------
# Build DSN
# ---------------------------------------------------------
def build_dsn() -> str:
    DB_PASSWORD_ESCAPED = quote_plus(DB_PASSWORD)

    return (
        f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD_ESCAPED}"
        f"@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
    )

DATABASE_URL = build_dsn()

# ---------------------------------------------------------
# Async SQLAlchemy Engine
# ---------------------------------------------------------
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    future=True,
)

# ---------------------------------------------------------
# AsyncSession
# ---------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ---------------------------------------------------------
# Test the database connection
# ---------------------------------------------------------
async def check_db_connection() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        log_debug(f"Database connection failed: {e}")
        return False

# ---------------------------------------------------------
# Run raw SQL from  original create_tables()
# ---------------------------------------------------------
async def create_tables():
    posts_table_sql = """
    CREATE TABLE IF NOT EXISTS public.posts (
        id BIGSERIAL PRIMARY KEY,
        platform VARCHAR(50) NOT NULL,
        external_id VARCHAR(255) NOT NULL,
        url VARCHAR(255) NOT NULL,
        title TEXT,
        content TEXT,
        author VARCHAR(50),
        published_at TIMESTAMP,
        scraped_at TIMESTAMP DEFAULT NOW(),
        score INT,
        summary TEXT,
        engagement JSONB,
        
        CONSTRAINT posts_unique
            UNIQUE (platform, external_id)
    );
    """

    logs_table_sql = """
    CREATE TABLE IF NOT EXISTS public.logs (
        id BIGSERIAL PRIMARY KEY,
        uuid VARCHAR(100) NOT NULL UNIQUE,
        event_type VARCHAR(50) NOT NULL,
        event_status VARCHAR(50),
        attempt_count INT DEFAULT 1,
        reason TEXT,
        metadata JSONB,
        created_by VARCHAR(100),
        created_at TIMESTAMP DEFAULT NOW()
    );
    """
    
    async with engine.begin() as conn:
        await conn.execute(text(posts_table_sql))
        await conn.execute(text(logs_table_sql))
        await conn.commit()       