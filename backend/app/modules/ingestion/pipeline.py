import asyncio

from bson import ObjectId

from app.core.database import get_mongo_db
from app.core.security import decrypt_secret
from app.models import collections as c
from app.models.common import utcnow
from app.modules.ingestion.ast_parser import parse_file, resolve_imports
from app.modules.ingestion.github_connector import (
    cleanup_clone,
    clone_repository,
    discover_source_files,
)
from app.modules.ingestion.graph_writer import write_repository_graph
from app.modules.search.index_writer import index_repository_components


async def run_ingestion(*, repository_id: str, job_id: str) -> None:
    """The whole pipeline for one repository: clone -> discover files -> parse
    each -> persist results -> update statuses. Runs inside an RQ worker
    process, never inline in an HTTP request — cloning and parsing a real
    repository is far too slow to do within a request/response cycle."""
    db = get_mongo_db()

    repo = await db[c.REPOSITORIES].find_one({"_id": ObjectId(repository_id)})
    if repo is None:
        return

    await db[c.INGESTION_JOBS].update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {"status": "running", "startedAt": utcnow()}},
    )
    await db[c.REPOSITORIES].update_one(
        {"_id": ObjectId(repository_id)}, {"$set": {"status": "syncing"}}
    )

    workdir = None
    try:
        access_token = decrypt_secret(repo["accessTokenEnc"]) if repo["accessTokenEnc"] else None
        workdir = clone_repository(
            repo["githubUrl"], access_token, branch=repo.get("defaultBranch", "main")
        )

        files = discover_source_files(workdir)
        language_stats: dict[str, int] = {}
        loc_count = 0
        components_found = 0
        parse_errors: list[str] = []
        parsed_files = []

        for absolute_path in files:
            relative_path = str(absolute_path.relative_to(workdir)).replace("\\", "/")
            parsed = parse_file(absolute_path, relative_path)

            if parsed.error:
                parse_errors.append(f"{relative_path}: {parsed.error}")
                continue

            language_stats[parsed.language] = language_stats.get(parsed.language, 0) + 1
            components_found += len(parsed.components)
            loc_count += absolute_path.read_text(encoding="utf-8", errors="ignore").count("\n") + 1
            parsed_files.append(parsed)

        # Import resolution needs the complete set of in-repo file paths to
        # match targets against, so it can only run once every file has been
        # parsed, not incrementally inside the loop above.
        all_relative_paths = {p.file_path for p in parsed_files}
        resolved_imports = resolve_imports(parsed_files, all_relative_paths)

        parsed_docs = [
            {
                "repositoryId": ObjectId(repository_id),
                "jobId": ObjectId(job_id),
                "filePath": parsed.file_path,
                "language": parsed.language,
                "imports": parsed.imports,
                "resolvedImports": resolved_imports.get(parsed.file_path, []),
                "components": [
                    {
                        "name": comp.name,
                        "type": comp.type,
                        "startLine": comp.start_line,
                        "endLine": comp.end_line,
                        # Lines-of-code proxy for complexity — cheap, transparent,
                        # and derivable from data already captured; a richer
                        # branch-counting metric is a documented future upgrade.
                        "complexityScore": comp.end_line - comp.start_line + 1,
                    }
                    for comp in parsed.components
                ],
            }
            for parsed in parsed_files
        ]

        # Replace, not append: a re-sync should reflect the current state of
        # the repo, not accumulate stale entries from a previous sync.
        await db[c.PARSED_FILES].delete_many({"repositoryId": ObjectId(repository_id)})
        if parsed_docs:
            await db[c.PARSED_FILES].insert_many(parsed_docs)

        await write_repository_graph(
            repository_id=repository_id,
            github_url=repo["githubUrl"],
            parsed_docs=parsed_docs,
        )

        # Chroma + sentence-transformers are synchronous, CPU-bound APIs (no
        # network I/O to await) — running via to_thread keeps this coroutine
        # from blocking the worker's event loop for the embedding duration.
        await asyncio.to_thread(
            index_repository_components,
            repository_id=repository_id,
            parsed_docs=parsed_docs,
        )

        stats = {
            "filesDiscovered": len(files),
            "filesParsed": len(parsed_docs),
            "componentsFound": components_found,
            "parseErrors": parse_errors,
            "byLanguage": language_stats,
        }

        await db[c.REPOSITORIES].update_one(
            {"_id": ObjectId(repository_id)},
            {
                "$set": {
                    "status": "ready",
                    "lastSyncedAt": utcnow(),
                    "languageStats": language_stats,
                    "locCount": loc_count,
                }
            },
        )
        await db[c.INGESTION_JOBS].update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"status": "succeeded", "finishedAt": utcnow(), "stats": stats}},
        )
    except Exception as exc:  # noqa: BLE001 - a failed job must be recorded, not crash the worker
        await db[c.REPOSITORIES].update_one(
            {"_id": ObjectId(repository_id)}, {"$set": {"status": "error"}}
        )
        await db[c.INGESTION_JOBS].update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"status": "failed", "finishedAt": utcnow(), "error": str(exc)}},
        )
    finally:
        if workdir is not None:
            cleanup_clone(workdir)
