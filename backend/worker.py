"""Runs the ingestion job worker. Usage: python worker.py

Uses rq's SimpleWorker rather than the default Worker — the default relies on
os.fork(), which doesn't exist on Windows and would crash immediately. Every
job still runs in isolation per-call, just without the extra process-fork
safety net; fine at this scale, worth revisiting if ingestion jobs start
taking down the whole worker on a bad crash.
"""

from rq.worker import SimpleWorker

from app.core.database import get_sync_redis_client
from app.worker.jobs import QUEUE_NAME, get_ingestion_queue

if __name__ == "__main__":
    connection = get_sync_redis_client()
    worker = SimpleWorker([get_ingestion_queue()], connection=connection)
    print(f"Worker listening on queue '{QUEUE_NAME}'...")
    worker.work()
