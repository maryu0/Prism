"""Create Mongo indexes and Neo4j constraints. Safe to re-run — everything is idempotent.

Usage: python -m scripts.init_db
"""

import asyncio

from app.core.graph_schema import create_neo4j_constraints
from app.core.indexes import create_mongo_indexes


async def main() -> None:
    print("Creating MongoDB indexes...")
    mongo_result = await create_mongo_indexes()
    for collection, names in mongo_result.items():
        print(f"  {collection}: {names}")

    print("\nApplying Neo4j constraints/indexes...")
    neo4j_result = await create_neo4j_constraints()
    for statement in neo4j_result:
        print(f"  {statement}")

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
