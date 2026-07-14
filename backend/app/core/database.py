from functools import lru_cache

import chromadb
import redis as sync_redis
from chromadb.api.models.Collection import Collection
from motor.motor_asyncio import AsyncIOMotorClient
from neo4j import AsyncDriver, AsyncGraphDatabase
from redis.asyncio import Redis, from_url

from app.core.config import get_settings

CODE_COMPONENTS_COLLECTION = "code_components"


@lru_cache
def get_mongo_client() -> AsyncIOMotorClient:
    settings = get_settings()
    # tz_aware=True: without it, PyMongo returns naive datetimes for BSON dates
    # (no tzinfo, even though they're stored as UTC), which crashes the moment you
    # compare them against a timezone-aware datetime.now(UTC) elsewhere in the app.
    return AsyncIOMotorClient(settings.mongodb_url, tz_aware=True)


def get_mongo_db():
    """Explicit db name — doesn't depend on the connection string's path segment,
    which Atlas's default copy-paste URL omits."""
    return get_mongo_client()["prism"]


@lru_cache
def get_neo4j_driver() -> AsyncDriver:
    settings = get_settings()
    return AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )


@lru_cache
def get_redis_client() -> Redis:
    settings = get_settings()
    return from_url(settings.redis_url, decode_responses=True)


@lru_cache
def get_sync_redis_client() -> sync_redis.Redis:
    """RQ (the job queue) predates asyncio and expects a synchronous redis-py
    connection — it's used only by the worker process and by code enqueueing
    jobs, never inside an async request handler."""
    settings = get_settings()
    return sync_redis.from_url(settings.redis_url, decode_responses=False)


@lru_cache
def get_chroma_client() -> chromadb.ClientAPI:
    """Chroma is embedded, not a network service — PersistentClient just
    reads/writes SQLite + vector index files under this directory. No
    account, no network round-trip, no cloud free-tier limits to hit."""
    settings = get_settings()
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)


def get_code_components_collection() -> Collection:
    """Cosine similarity, not Chroma's default L2 distance: embeddings from
    Sentence-Transformers models like all-MiniLM-L6-v2 are trained and
    evaluated for cosine similarity, so results rank correctly only with
    that metric explicitly requested here."""
    return get_chroma_client().get_or_create_collection(
        name=CODE_COMPONENTS_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


async def check_mongo() -> bool:
    await get_mongo_client().admin.command("ping")
    return True


async def check_neo4j() -> bool:
    async with get_neo4j_driver().session() as session:
        await session.run("RETURN 1")
    return True


async def check_redis() -> bool:
    return await get_redis_client().ping()


async def check_chroma() -> bool:
    # Chroma's client is synchronous (it's embedded, no network I/O to await)
    get_code_components_collection().count()
    return True
