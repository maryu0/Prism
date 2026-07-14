import uuid

from app.core.database import get_code_components_collection
from app.modules.search.embeddings import component_to_text, embed_text
from app.modules.search.index_writer import index_repository_components, search_components


def test_embed_text_returns_a_fixed_size_vector():
    vector = embed_text("function main in src/main.py")

    assert isinstance(vector, list)
    assert len(vector) == 384  # all-MiniLM-L6-v2's output dimension
    assert all(isinstance(x, float) for x in vector)


def test_embed_text_is_deterministic():
    a = embed_text("function main in src/main.py")
    b = embed_text("function main in src/main.py")

    assert a == b


def test_component_to_text_includes_type_name_and_path():
    text = component_to_text(
        name="validate_token", type_="function", file_path="app/core/security.py", imports=[]
    )

    assert "validate_token" in text
    assert "function" in text
    assert "app/core/security.py" in text


def _cleanup_repo_index(repository_id: str) -> None:
    get_code_components_collection().delete(where={"repositoryId": repository_id})


def test_index_and_search_finds_semantically_related_component():
    repository_id = f"test-repo-{uuid.uuid4().hex[:8]}"
    parsed_docs = [
        {
            "filePath": "app/core/security.py",
            "language": "python",
            "imports": [],
            "components": [
                {
                    "name": "verify_password",
                    "type": "function",
                    "startLine": 10,
                    "endLine": 12,
                },
                {
                    "name": "render_homepage",
                    "type": "function",
                    "startLine": 1,
                    "endLine": 5,
                },
            ],
        }
    ]

    try:
        index_repository_components(repository_id=repository_id, parsed_docs=parsed_docs)

        results = search_components(
            workspace_repository_ids=[repository_id],
            query="checking if a user's login credentials are correct",
            limit=5,
        )

        assert len(results) == 2
        # The password-checking function should rank above the unrelated
        # homepage-rendering function for a login-credentials query.
        names_in_order = [r["name"] for r in results]
        assert names_in_order[0] == "verify_password"
    finally:
        _cleanup_repo_index(repository_id)


def test_search_is_scoped_to_given_repository_ids():
    repo_a = f"test-repo-{uuid.uuid4().hex[:8]}"
    repo_b = f"test-repo-{uuid.uuid4().hex[:8]}"
    parsed_docs = [
        {
            "filePath": "src/only.py",
            "language": "python",
            "imports": [],
            "components": [
                {"name": "unique_marker_fn", "type": "function", "startLine": 1, "endLine": 2}
            ],
        }
    ]

    try:
        index_repository_components(repository_id=repo_a, parsed_docs=parsed_docs)

        # Searching scoped only to repo_b must not surface repo_a's component,
        # even though it's the closest match in the whole collection — this is
        # the workspace-isolation guarantee search_components exists to provide.
        results = search_components(
            workspace_repository_ids=[repo_b], query="unique marker fn", limit=5
        )

        assert results == []
    finally:
        _cleanup_repo_index(repo_a)
        _cleanup_repo_index(repo_b)
