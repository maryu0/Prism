from app.core.database import get_code_components_collection
from app.modules.ingestion.graph_writer import component_id
from app.modules.search.embeddings import component_to_text, embed_texts


def index_repository_components(*, repository_id: str, parsed_docs: list[dict]) -> None:
    """Embeds every parsed component and upserts it into Chroma. Reuses the
    same deterministic id scheme as the Neo4j graph writer (repositoryId +
    filePath + type + name) so a component's identity is the same string
    across Mongo, Neo4j, and Chroma — no separate id-mapping table needed to
    join results from one store back to another."""
    collection = get_code_components_collection()

    # Delete-then-rewrite, same reasoning as parsedFiles (Mongo) and the
    # Neo4j subgraph: a re-sync should reflect exactly the current repo,
    # not accumulate embeddings for components that no longer exist.
    collection.delete(where={"repositoryId": repository_id})

    ids: list[str] = []
    texts: list[str] = []
    metadatas: list[dict] = []

    for doc in parsed_docs:
        file_path = doc["filePath"]
        for comp in doc["components"]:
            cid = component_id(repository_id, file_path, comp["name"], comp["type"])
            ids.append(cid)
            texts.append(
                component_to_text(
                    name=comp["name"],
                    type_=comp["type"],
                    file_path=file_path,
                    imports=doc.get("imports", []),
                )
            )
            metadatas.append(
                {
                    "repositoryId": repository_id,
                    "filePath": file_path,
                    "name": comp["name"],
                    "type": comp["type"],
                    "startLine": comp["startLine"],
                    "endLine": comp["endLine"],
                }
            )

    if not ids:
        return

    embeddings = embed_texts(texts)
    collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)


def search_components(
    *, workspace_repository_ids: list[str], query: str, limit: int = 10
) -> list[dict]:
    """Semantic search scoped to a set of repository ids (i.e. only repos in
    the caller's workspace) so one workspace can never retrieve another
    workspace's code through search, even though Chroma has a single shared
    collection across all repositories."""
    if not workspace_repository_ids:
        return []

    collection = get_code_components_collection()
    query_embedding = embed_texts([query])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit,
        where={"repositoryId": {"$in": workspace_repository_ids}},
    )

    matches = []
    ids = results["ids"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    for cid, metadata, distance in zip(ids, metadatas, distances, strict=True):
        matches.append(
            {
                "id": cid,
                "repositoryId": metadata["repositoryId"],
                "filePath": metadata["filePath"],
                "name": metadata["name"],
                "type": metadata["type"],
                "startLine": metadata["startLine"],
                "endLine": metadata["endLine"],
                # Cosine distance -> similarity: collection is configured with
                # hnsw:space=cosine, where Chroma returns distance = 1 - cosine
                # similarity. Converting back to similarity (0..1, higher =
                # more relevant) is far more intuitive for an API response
                # than a raw distance number.
                "similarity": 1 - distance,
            }
        )
    return matches
