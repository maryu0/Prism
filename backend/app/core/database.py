from functools import lru_cache

from motor.motor_asyncio import AsyncIOMotorClient
from neo4j import AsyncDriver, AsyncGraphDatabase
from redis.asyncio import Redis, from_url

from app.core.config import get_settings


@lru_cache
def get_mongo_client() -> AsyncIOMotorClient:
    settings = get_settings()
    return AsyncIOMotorClient(settings.mongodb_url)


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


async def check_mongo() -> bool:
    await get_mongo_client().admin.command("ping")
    return True


async def check_neo4j() -> bool:
    async with get_neo4j_driver().session() as session:
        await session.run("RETURN 1")
    return True


async def check_redis() -> bool:
    return await get_redis_client().ping()
