from app.core.database import get_neo4j_driver


def component_id(repository_id: str, file_path: str, name: str, type_: str) -> str:
    """Deterministic id, prefixed with repositoryId so the same function/class
    name in two different repos never collides on Neo4j's global CodeComponent.id
    uniqueness constraint. Same file+name+type on a re-sync yields the same id,
    which is what lets MERGE below dedupe instead of creating duplicate nodes."""
    return f"{repository_id}:{file_path}:{type_}:{name}"


def file_id(repository_id: str, file_path: str) -> str:
    return f"{repository_id}:{file_path}"


async def write_repository_graph(
    *, repository_id: str, github_url: str, parsed_docs: list[dict]
) -> None:
    """Replaces this repository's entire subgraph. Mirrors the same
    'delete then reinsert' strategy already used for the parsedFiles Mongo
    collection on re-sync: simpler and safer than diffing old vs. new nodes,
    at the cost of briefly having no graph data for this repo mid-write."""
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

        await session.run(
            "MERGE (r:Repository {id: $repository_id}) SET r.githubUrl = $github_url",
            repository_id=repository_id,
            github_url=github_url,
        )

        for doc in parsed_docs:
            file_path = doc["filePath"]
            fid = file_id(repository_id, file_path)

            await session.run(
                """
                MATCH (r:Repository {id: $repository_id})
                MERGE (f:File {id: $file_id})
                SET f.path = $file_path, f.language = $language
                MERGE (r)-[:HAS_FILE]->(f)
                """,
                repository_id=repository_id,
                file_id=fid,
                file_path=file_path,
                language=doc["language"],
            )

            for comp in doc["components"]:
                cid = component_id(repository_id, file_path, comp["name"], comp["type"])
                await session.run(
                    """
                    MATCH (f:File {id: $file_id})
                    MERGE (comp:CodeComponent {id: $comp_id})
                    SET comp.name = $name,
                        comp.type = $type,
                        comp.filePath = $file_path,
                        comp.startLine = $start_line,
                        comp.endLine = $end_line,
                        comp.complexityScore = $complexity_score
                    MERGE (f)-[:DEFINES]->(comp)
                    """,
                    file_id=fid,
                    comp_id=cid,
                    name=comp["name"],
                    type=comp["type"],
                    file_path=file_path,
                    start_line=comp["startLine"],
                    end_line=comp["endLine"],
                    complexity_score=comp.get("complexityScore", 0),
                )

        # Import edges need every File node to already exist, so this is a
        # second pass over all docs rather than being folded into the loop
        # above — an import target processed before its source file would
        # otherwise have nothing to MATCH against.
        for doc in parsed_docs:
            src_id = file_id(repository_id, doc["filePath"])
            for target_path in doc.get("resolvedImports", []):
                dst_id = file_id(repository_id, target_path)
                await session.run(
                    """
                    MATCH (src:File {id: $src_id})
                    MATCH (dst:File {id: $dst_id})
                    MERGE (src)-[:IMPORTS]->(dst)
                    """,
                    src_id=src_id,
                    dst_id=dst_id,
                )
