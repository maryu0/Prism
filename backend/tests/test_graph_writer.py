import uuid

import pytest

from app.core.database import get_neo4j_driver
from app.modules.ingestion.graph_writer import component_id, file_id, write_repository_graph


def test_component_id_is_deterministic_and_repo_scoped():
    a = component_id("repo1", "src/foo.py", "bar", "function")
    b = component_id("repo1", "src/foo.py", "bar", "function")
    c = component_id("repo2", "src/foo.py", "bar", "function")

    assert a == b
    assert a != c


def test_file_id_is_deterministic():
    assert file_id("repo1", "src/foo.py") == file_id("repo1", "src/foo.py")
    assert file_id("repo1", "a.py") != file_id("repo2", "a.py")


async def _cleanup_repo_graph(repository_id: str) -> None:
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


@pytest.mark.asyncio(loop_scope="session")
async def test_write_repository_graph_creates_nodes_and_relationships():
    repository_id = f"test-repo-{uuid.uuid4().hex[:8]}"
    parsed_docs = [
        {
            "filePath": "src/main.py",
            "language": "python",
            "components": [
                {"name": "main", "type": "function", "startLine": 1, "endLine": 5},
                {"name": "Widget", "type": "class", "startLine": 7, "endLine": 20},
            ],
        }
    ]

    try:
        await write_repository_graph(
            repository_id=repository_id,
            github_url="https://github.com/test/repo",
            parsed_docs=parsed_docs,
        )

        driver = get_neo4j_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (r:Repository {id: $repository_id})-[:HAS_FILE]->(f:File)
                      -[:DEFINES]->(comp:CodeComponent)
                RETURN comp.name AS name, comp.type AS type
                ORDER BY name
                """,
                repository_id=repository_id,
            )
            records = [dict(r) async for r in result]

        assert records == [
            {"name": "Widget", "type": "class"},
            {"name": "main", "type": "function"},
        ]
    finally:
        await _cleanup_repo_graph(repository_id)


@pytest.mark.asyncio(loop_scope="session")
async def test_write_repository_graph_is_idempotent_on_resync():
    repository_id = f"test-repo-{uuid.uuid4().hex[:8]}"
    first_docs = [
        {
            "filePath": "src/old.py",
            "language": "python",
            "components": [
                {"name": "old_func", "type": "function", "startLine": 1, "endLine": 2}
            ],
        }
    ]
    second_docs = [
        {
            "filePath": "src/new.py",
            "language": "python",
            "components": [
                {"name": "new_func", "type": "function", "startLine": 1, "endLine": 2}
            ],
        }
    ]

    try:
        await write_repository_graph(
            repository_id=repository_id,
            github_url="https://github.com/test/repo",
            parsed_docs=first_docs,
        )
        await write_repository_graph(
            repository_id=repository_id,
            github_url="https://github.com/test/repo",
            parsed_docs=second_docs,
        )

        driver = get_neo4j_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (r:Repository {id: $repository_id})-[:HAS_FILE]->(f:File)
                      -[:DEFINES]->(comp:CodeComponent)
                RETURN comp.name AS name
                """,
                repository_id=repository_id,
            )
            names = [record["name"] async for record in result]

        # A re-sync must reflect only the current state — the old component
        # from the first sync must not linger alongside the new one.
        assert names == ["new_func"]
    finally:
        await _cleanup_repo_graph(repository_id)


@pytest.mark.asyncio(loop_scope="session")
async def test_write_repository_graph_sets_complexity_score():
    repository_id = f"test-repo-{uuid.uuid4().hex[:8]}"
    parsed_docs = [
        {
            "filePath": "src/main.py",
            "language": "python",
            "components": [
                {
                    "name": "main",
                    "type": "function",
                    "startLine": 1,
                    "endLine": 10,
                    "complexityScore": 10,
                },
            ],
        }
    ]

    try:
        await write_repository_graph(
            repository_id=repository_id,
            github_url="https://github.com/test/repo",
            parsed_docs=parsed_docs,
        )

        driver = get_neo4j_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (comp:CodeComponent {id: $comp_id})
                RETURN comp.complexityScore AS complexityScore
                """,
                comp_id=component_id(repository_id, "src/main.py", "main", "function"),
            )
            record = await result.single()

        assert record["complexityScore"] == 10
    finally:
        await _cleanup_repo_graph(repository_id)


@pytest.mark.asyncio(loop_scope="session")
async def test_write_repository_graph_creates_imports_relationship():
    repository_id = f"test-repo-{uuid.uuid4().hex[:8]}"
    parsed_docs = [
        {
            "filePath": "src/main.py",
            "language": "python",
            "components": [],
            "resolvedImports": ["src/utils.py"],
        },
        {
            "filePath": "src/utils.py",
            "language": "python",
            "components": [],
            "resolvedImports": [],
        },
    ]

    try:
        await write_repository_graph(
            repository_id=repository_id,
            github_url="https://github.com/test/repo",
            parsed_docs=parsed_docs,
        )

        driver = get_neo4j_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (src:File {id: $src_id})-[:IMPORTS]->(dst:File {id: $dst_id})
                RETURN count(*) AS edgeCount
                """,
                src_id=file_id(repository_id, "src/main.py"),
                dst_id=file_id(repository_id, "src/utils.py"),
            )
            record = await result.single()

        assert record["edgeCount"] == 1
    finally:
        await _cleanup_repo_graph(repository_id)


@pytest.mark.asyncio(loop_scope="session")
async def test_write_repository_graph_imports_idempotent_on_resync():
    repository_id = f"test-repo-{uuid.uuid4().hex[:8]}"
    parsed_docs = [
        {
            "filePath": "src/main.py",
            "language": "python",
            "components": [],
            "resolvedImports": ["src/utils.py"],
        },
        {
            "filePath": "src/utils.py",
            "language": "python",
            "components": [],
            "resolvedImports": [],
        },
    ]

    try:
        await write_repository_graph(
            repository_id=repository_id,
            github_url="https://github.com/test/repo",
            parsed_docs=parsed_docs,
        )
        await write_repository_graph(
            repository_id=repository_id,
            github_url="https://github.com/test/repo",
            parsed_docs=parsed_docs,
        )

        driver = get_neo4j_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (src:File {id: $src_id})-[r:IMPORTS]->(dst:File {id: $dst_id})
                RETURN count(r) AS edgeCount
                """,
                src_id=file_id(repository_id, "src/main.py"),
                dst_id=file_id(repository_id, "src/utils.py"),
            )
            record = await result.single()

        assert record["edgeCount"] == 1
    finally:
        await _cleanup_repo_graph(repository_id)
