import asyncio

from rq import Queue

from app.core.database import get_sync_redis_client
from app.modules.ingestion.pipeline import run_ingestion

QUEUE_NAME = "ingestion"

# A single event loop reused for every job this worker process runs. Motor's
# client is cached per-process (see get_mongo_client), so it becomes bound to
# whichever event loop is running the first time it's used. asyncio.run() per
# job would create then close a fresh loop every call, leaving that cached
# client attached to a dead loop for every job after the first — this loop is
# created once and kept alive for the worker's entire lifetime instead.
_worker_loop = asyncio.new_event_loop()


def get_ingestion_queue() -> Queue:
    return Queue(QUEUE_NAME, connection=get_sync_redis_client())


def run_ingestion_job(repository_id: str, job_id: str) -> None:
    """RQ workers call plain synchronous functions — this is the sync
    entrypoint the queue actually invokes, wrapping the real async pipeline
    (which needs an event loop for Motor) by running it on this worker
    process's single long-lived event loop."""
    _worker_loop.run_until_complete(run_ingestion(repository_id=repository_id, job_id=job_id))
