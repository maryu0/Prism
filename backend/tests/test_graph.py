import uuid

import pytest
from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.core.database import get_mongo_db, get_neo4j_driver
from app.main import app
from app.models import collections as c

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@test.prism"


async def _register_and_login(client: AsyncClient, tracker: dict) -> dict:
    email = unique_email("graphadmin")
    tracker["emails"].append(email)
    register = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpass123", "name": "Graph Admin"},
    )
    workspace_id = register.json()["workspaceId"]
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "testpass123"}
    )
    access_token = login.json()["accessToken"]
    return {"workspace_id": workspace_id, "headers": {"Authorization": f"Bearer {access_token}"}}


async def _cleanup(tracker: dict, repository_id: str | None) -> None:
    db = get_mongo_db()
    emails = tracker["emails"]
    if emails:
        users = await db[c.USERS].find({"email": {"$in": emails}}).to_list(length=None)
        owner_ids = [u["_id"] for u in users]
        await db[c.USERS].delete_many({"email": {"$in": emails}})
        if owner_ids:
            await db[c.WORKSPACES].delete_many({"ownerId": {"$in": owner_ids}})
    if tracker["repo_ids"]:
        await db[c.REPOSITORIES].delete_many({"_id": {"$in": tracker["repo_ids"]}})

    if repository_id:
        driver = get_neo4j_driver()
        async with driver.session() as session:
            await session.run(
                """
                MATCH (r:Repository {id: $repository_id})
                OPTIONAL MATCH (r)-[:HAS_FILE]->(f:File)
                OPTIONAL MATCH (f)-[:DEFINES]->(comp:CodeComponent)
                DETACH DELETE r, f, comp
                """,
                repository_id=repository_id,
            )


async def test_get_graph_returns_nodes_and_edges_for_owned_repository(client):
    from app.modules.ingestion.graph_writer import write_repository_graph

    tracker = {"emails": [], "repo_ids": []}
    auth = await _register_and_login(client, tracker)

    db = get_mongo_db()
    repo_id = ObjectId()
    tracker["repo_ids"].append(repo_id)
    await db[c.REPOSITORIES].insert_one(
        {
            "_id": repo_id,
            "workspaceId": ObjectId(auth["workspace_id"]),
            "githubUrl": "https://github.com/test/graph-repo",
            "defaultBranch": "main",
            "accessTokenEnc": "",
            "status": "ready",
            "languageStats": {},
            "locCount": 0,
        }
    )

    repository_id = str(repo_id)
    try:
        await write_repository_graph(
            repository_id=repository_id,
            github_url="https://github.com/test/graph-repo",
            parsed_docs=[
                {
                    "filePath": "a.py",
                    "language": "python",
                    "components": [
                        {"name": "a_func", "type": "function", "startLine": 1, "endLine": 5,
                         "complexityScore": 5}
                    ],
                    "resolvedImports": [],
                },
                {
                    "filePath": "b.py",
                    "language": "python",
                    "components": [
                        {"name": "b_func", "type": "function", "startLine": 1, "endLine": 10,
                         "complexityScore": 10}
                    ],
                    "resolvedImports": ["a.py"],
                },
            ],
        )

        response = await client.get(
            f"/api/v1/repositories/{repository_id}/graph", headers=auth["headers"]
        )

        assert response.status_code == 200
        body = response.json()
        assert body["repositoryId"] == repository_id
        assert body["truncated"] is False

        node_paths = {n["path"] for n in body["nodes"]}
        assert node_paths == {"a.py", "b.py"}

        node_a = next(n for n in body["nodes"] if n["path"] == "a.py")
        assert node_a["componentCount"] == 1
        assert node_a["avgComplexity"] == 5.0

        edge = next(e for e in body["edges"])
        b_id = next(n["id"] for n in body["nodes"] if n["path"] == "b.py")
        a_id = next(n["id"] for n in body["nodes"] if n["path"] == "a.py")
        assert edge == {"source": b_id, "target": a_id, "type": "IMPORTS"}

        components_response = await client.get(
            f"/api/v1/repositories/{repository_id}/graph/file-components",
            params={"file_id": a_id},
            headers=auth["headers"],
        )
        assert components_response.status_code == 200
        components_body = components_response.json()
        assert components_body["fileId"] == a_id
        assert components_body["components"] == [
            {
                "name": "a_func",
                "type": "function",
                "startLine": 1,
                "endLine": 5,
                "complexityScore": 5,
            }
        ]
    finally:
        await _cleanup(tracker, repository_id)


async def test_get_file_components_defaults_missing_complexity_score_to_zero(client):
    """Regression test: CodeComponent nodes written before complexity scoring
    existed have complexityScore = null in Neo4j. The endpoint must not 500
    on this stale, real-world data."""
    tracker = {"emails": [], "repo_ids": []}
    auth = await _register_and_login(client, tracker)

    db = get_mongo_db()
    repo_id = ObjectId()
    tracker["repo_ids"].append(repo_id)
    await db[c.REPOSITORIES].insert_one(
        {
            "_id": repo_id,
            "workspaceId": ObjectId(auth["workspace_id"]),
            "githubUrl": "https://github.com/test/stale-repo",
            "defaultBranch": "main",
            "accessTokenEnc": "",
            "status": "ready",
            "languageStats": {},
            "locCount": 0,
        }
    )
    repository_id = str(repo_id)
    file_id = f"{repository_id}:legacy.py"

    try:
        driver = get_neo4j_driver()
        async with driver.session() as session:
            await session.run(
                """
                MERGE (r:Repository {id: $repository_id})
                MERGE (f:File {id: $file_id})
                MERGE (r)-[:HAS_FILE]->(f)
                SET f.path = 'legacy.py', f.language = 'python'
                MERGE (f)-[:DEFINES]->(comp:CodeComponent {id: $file_id + ':legacy_func'})
                SET comp.name = 'legacy_func', comp.type = 'function',
                    comp.startLine = 1, comp.endLine = 3, comp.complexityScore = null
                """,
                repository_id=repository_id,
                file_id=file_id,
            )

            response = await client.get(
                f"/api/v1/repositories/{repository_id}/graph/file-components",
                params={"file_id": file_id},
                headers=auth["headers"],
            )

            assert response.status_code == 200
            body = response.json()
            assert body["components"] == [
                {
                    "name": "legacy_func",
                    "type": "function",
                    "startLine": 1,
                    "endLine": 3,
                    "complexityScore": 0,
                }
            ]
    finally:
        await _cleanup(tracker, repository_id)


async def test_get_graph_404_for_repository_in_another_workspace(client):
    tracker_owner = {"emails": [], "repo_ids": []}
    tracker_other = {"emails": [], "repo_ids": []}
    owner_auth = await _register_and_login(client, tracker_owner)
    other_auth = await _register_and_login(client, tracker_other)

    db = get_mongo_db()
    repo_id = ObjectId()
    tracker_owner["repo_ids"].append(repo_id)
    await db[c.REPOSITORIES].insert_one(
        {
            "_id": repo_id,
            "workspaceId": ObjectId(owner_auth["workspace_id"]),
            "githubUrl": "https://github.com/test/private-repo",
            "defaultBranch": "main",
            "accessTokenEnc": "",
            "status": "ready",
            "languageStats": {},
            "locCount": 0,
        }
    )

    try:
        response = await client.get(
            f"/api/v1/repositories/{repo_id}/graph", headers=other_auth["headers"]
        )
        assert response.status_code == 404
    finally:
        await _cleanup(tracker_owner, None)
        await _cleanup(tracker_other, None)
