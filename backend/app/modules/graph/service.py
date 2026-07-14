from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import get_mongo_db, get_neo4j_driver
from app.models import collections as c

DEFAULT_FILE_LIMIT = 300


async def get_repository_graph(
    *, repository_id: str, workspace_id: str, file_limit: int = DEFAULT_FILE_LIMIT
) -> dict:
    """File-level lineage graph (nodes = Files, edges = IMPORTS). CodeComponents
    are folded into per-file metadata (componentCount, avgComplexity) rather
    than rendered as their own graph nodes — a repo with thousands of
    functions would make a component-level graph unusable in the browser."""
    db = get_mongo_db()
    repo = await db[c.REPOSITORIES].find_one(
        {"_id": ObjectId(repository_id), "workspaceId": ObjectId(workspace_id)}
    )
    if not repo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repository not found")

    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (r:Repository {id: $repository_id})-[:HAS_FILE]->(f:File)
            WITH r, f
            LIMIT $file_limit
            OPTIONAL MATCH (f)-[:DEFINES]->(comp:CodeComponent)
            WITH f, count(comp) AS componentCount,
                 coalesce(avg(comp.complexityScore), 0.0) AS avgComplexity
            OPTIONAL MATCH (f)-[:IMPORTS]->(f2:File)
            RETURN f.id AS id, f.path AS path, f.language AS language,
                   componentCount, avgComplexity,
                   collect(DISTINCT f2.id) AS importedFileIds
            """,
            repository_id=repository_id,
            file_limit=file_limit,
        )
        records = [dict(r) async for r in result]

    node_ids = {r["id"] for r in records}
    nodes = [
        {
            "id": r["id"],
            "label": r["path"].split("/")[-1],
            "path": r["path"],
            "language": r["language"] or "unknown",
            "componentCount": r["componentCount"],
            "avgComplexity": round(r["avgComplexity"], 1),
        }
        for r in records
    ]
    edges = [
        {"source": r["id"], "target": target_id, "type": "IMPORTS"}
        for r in records
        for target_id in r["importedFileIds"]
        # Only keep edges to files that are actually in the returned node
        # set — an import target beyond file_limit would otherwise dangle.
        if target_id in node_ids
    ]

    return {
        "repositoryId": repository_id,
        "nodes": nodes,
        "edges": edges,
        "truncated": len(records) >= file_limit,
    }


async def get_file_components(
    *, repository_id: str, workspace_id: str, file_id: str
) -> dict:
    """Component-level drill-down for a single file node, fetched lazily on
    click rather than embedding every component in the main graph payload —
    a repo with thousands of functions would bloat that response for data
    the user only needs after clicking a specific file."""
    db = get_mongo_db()
    repo = await db[c.REPOSITORIES].find_one(
        {"_id": ObjectId(repository_id), "workspaceId": ObjectId(workspace_id)}
    )
    if not repo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repository not found")

    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (f:File {id: $file_id})
            WHERE f.id STARTS WITH $repository_id + ':'
            OPTIONAL MATCH (f)-[:DEFINES]->(comp:CodeComponent)
            RETURN comp.name AS name, comp.type AS type,
                   comp.startLine AS startLine, comp.endLine AS endLine,
                   comp.complexityScore AS complexityScore
            ORDER BY comp.startLine
            """,
            file_id=file_id,
            repository_id=repository_id,
        )
        records = [dict(r) async for r in result if r["name"] is not None]

    return {
        "fileId": file_id,
        "components": [
            {
                "name": r["name"],
                "type": r["type"],
                "startLine": r["startLine"],
                "endLine": r["endLine"],
                "complexityScore": r["complexityScore"],
            }
            for r in records
        ],
    }
