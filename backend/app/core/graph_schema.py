from app.core.database import get_neo4j_driver

# Single-property uniqueness constraints only — Aura Free (Community-tier constraints)
# doesn't support composite node-key constraints. Cross-repository uniqueness for
# CodeComponent.id is instead guaranteed at the application layer by prefixing the
# repositoryId into the id itself when components are written (Phase 4).
CONSTRAINTS = [
    "CREATE CONSTRAINT code_component_id_unique IF NOT EXISTS "
    "FOR (c:CodeComponent) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT person_email_unique IF NOT EXISTS "
    "FOR (p:Person) REQUIRE p.email IS UNIQUE",
    "CREATE CONSTRAINT documentation_id_unique IF NOT EXISTS "
    "FOR (d:Documentation) REQUIRE d.id IS UNIQUE",
]

INDEXES = [
    "CREATE FULLTEXT INDEX code_component_name_search IF NOT EXISTS "
    "FOR (c:CodeComponent) ON EACH [c.name]",
]


async def create_neo4j_constraints() -> list[str]:
    """Idempotent — every statement uses IF NOT EXISTS, safe to re-run."""
    applied = []
    async with get_neo4j_driver().session() as session:
        for statement in CONSTRAINTS + INDEXES:
            await session.run(statement)
            applied.append(statement)
    return applied
