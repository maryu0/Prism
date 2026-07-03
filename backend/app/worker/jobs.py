import asyncio

from rq import Queue

from app.core.database import get_sync_redis_client
from app.modules.ingestion.pipeline import run_ingestion

QUEUE_NAME = "ingestion"


def get_ingestion_queue() -> Queue:
    return Queue(QUEUE_NAME, connection=get_sync_redis_client())


def run_ingestion_job(repository_id: str, job_id: str) -> None:
    """RQ workers call plain synchronous functions — this is the sync
    entrypoint the queue actually invokes, wrapping the real async pipeline
    (which needs an event loop for Motor) with asyncio.run()."""
    asyncio.run(run_ingestion(repository_id=repository_id, job_id=job_id))
