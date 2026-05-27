from contextlib import asynccontextmanager
from urllib.parse import quote_plus
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from loguru import logger
from .config import settings

_client: AsyncIOMotorClient | None = None


def _build_mongo_url() -> str:
    """Build MongoDB URL with properly percent-encoded credentials."""
    user = quote_plus(settings.MONGO_USERNAME)
    pwd = quote_plus(settings.MONGO_PASSWORD)
    host = settings.MONGO_HOST
    port = settings.MONGO_PORT
    db = settings.DB_NAME
    return f"mongodb://{user}:{pwd}@{host}:{port}/{db}?authSource=admin"


def get_client() -> AsyncIOMotorClient:
    if _client is None:
        raise RuntimeError("Database not initialized")
    return _client


def get_database():
    return get_client()[settings.DB_NAME]


def get_gridfs() -> AsyncIOMotorGridFSBucket:
    db = get_database()
    return AsyncIOMotorGridFSBucket(db, bucket_name=settings.GRIDFS_BUCKET)


@asynccontextmanager
async def lifespan(app):
    global _client
    logger.info("Connecting to MongoDB...")
    _client = AsyncIOMotorClient(_build_mongo_url())
    await _client.admin.command("ping")
    logger.info("MongoDB connected")

    db = get_database()
    await db.users.create_index("email", unique=True)
    await db.questions.create_index([("difficulty", 1), ("type", 1), ("is_active", 1)])
    await db.quiz_sessions.create_index([("user_id", 1), ("status", 1)])
    await db.audit_logs.create_index([("user_id", 1), ("timestamp", -1)])
    logger.info("Indexes ensured")

    yield

    logger.info("Closing MongoDB connection...")
    _client.close()
