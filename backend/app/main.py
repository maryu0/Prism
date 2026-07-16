from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import check_chroma, check_mongo, check_neo4j, check_redis
from app.modules.analytics.router import router as analytics_router
from app.modules.audit_log.router import router as audit_log_router
from app.modules.auth.router import router as auth_router
from app.modules.chat.router import router as chat_router
from app.modules.learning_paths.router import router as learning_paths_router
from app.modules.notifications.router import router as notifications_router
from app.modules.repositories.router import router as repositories_router
from app.modules.search.router import router as search_router

settings = get_settings()

app = FastAPI(title="Prism API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(repositories_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(learning_paths_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(audit_log_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"service": "prism-api", "status": "ok"}


@app.get("/health")
async def health():
    checks = {}
    checks_to_run = (
        ("mongo", check_mongo),
        ("neo4j", check_neo4j),
        ("redis", check_redis),
        ("chroma", check_chroma),
    )
    for name, fn in checks_to_run:
        try:
            await fn()
            checks[name] = "ok"
        except Exception as exc:  # noqa: BLE001 - health check must never 500
            checks[name] = f"unreachable: {exc.__class__.__name__}"
    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}
