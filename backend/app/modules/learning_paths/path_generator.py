from dataclasses import dataclass, field

from app.core.database import get_neo4j_driver

# Base module-count target by self-reported experience level, before the
# role multiplier below is applied. Junior developers get more, smaller
# modules with intro docs; seniors get fewer, denser, code-only modules.
_BASE_MODULE_COUNT = {"junior": 12, "mid": 8, "senior": 5}
_INTRO_DOC_MODULE_COUNT = {"junior": 2, "mid": 1, "senior": 0}

# A "senior" *role* (an experienced hire onboarding onto a new codebase,
# distinct from self-reported experience_level) needs less hand-holding
# regardless of how they rated their own experience.
_ROLE_MULTIPLIER = {"developer": 1.0, "senior": 0.7}

MINUTES_PER_LOC = 0.5
MODULE_OVERHEAD_MINUTES = {"code_area": 10, "doc": 5, "task": 5}
MIN_ESTIMATED_MINUTES = 10


@dataclass
class CandidateFile:
    file_id: str
    file_path: str
    component_count: int
    total_complexity: int
    incoming_dependency_count: int
    dependency_file_ids: list[str] = field(default_factory=list)


@dataclass
class GeneratedModule:
    title: str
    description: str
    type: str
    target_entity_ids: list[str]
    order: int
    prerequisite_indices: list[int]  # indices into the returned module list, resolved by caller
    estimated_minutes: int


async def fetch_candidate_files(*, repository_id: str) -> list[CandidateFile]:
    """Pulls every file with at least one CodeComponent, ranked by fan-in
    (how many other files import it — the "hub" heuristic for structural
    criticality) then by aggregate complexity as a tiebreak."""
    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (r:Repository {id: $repository_id})-[:HAS_FILE]->(f:File)
            OPTIONAL MATCH (f)-[:DEFINES]->(comp:CodeComponent)
            WITH f, count(comp) AS componentCount,
                 coalesce(sum(comp.complexityScore), 0) AS totalComplexity
            WHERE componentCount > 0
            OPTIONAL MATCH (f)<-[:IMPORTS]-(dependent:File)
            WITH f, componentCount, totalComplexity,
                 count(DISTINCT dependent) AS incomingDependencyCount
            OPTIONAL MATCH (f)-[:IMPORTS]->(dep:File)
            WITH f, componentCount, totalComplexity, incomingDependencyCount,
                 collect(DISTINCT dep.id) AS dependencyFileIds
            RETURN f.id AS fileId, f.path AS filePath,
                   componentCount, totalComplexity, incomingDependencyCount,
                   dependencyFileIds
            ORDER BY incomingDependencyCount DESC, totalComplexity DESC
            """,
            repository_id=repository_id,
        )
        records = [dict(r) async for r in result]

    return [
        CandidateFile(
            file_id=r["fileId"],
            file_path=r["filePath"],
            component_count=r["componentCount"],
            total_complexity=r["totalComplexity"],
            incoming_dependency_count=r["incomingDependencyCount"],
            dependency_file_ids=r["dependencyFileIds"],
        )
        for r in records
    ]


def _target_module_count(*, role: str, experience_level: str) -> int:
    base = _BASE_MODULE_COUNT.get(experience_level, _BASE_MODULE_COUNT["mid"])
    multiplier = _ROLE_MULTIPLIER.get(role, 1.0)
    return max(1, round(base * multiplier))


def _topological_order(selected: list[CandidateFile]) -> list[CandidateFile]:
    """Kahn's algorithm over the dependency edges restricted to the selected
    file set only — a selected file's prerequisite is another *selected*
    file it imports; dependencies on unselected files are simply not
    represented, since there's no module covering them.

    Cycle handling: real codebases can have circular imports. Any file left
    over after the main pass (nonzero in-degree because it's stuck in a
    cycle) is appended in its original (criticality) order rather than
    failing generation — a deterministic, documented compromise, not a
    silent one."""
    selected_ids = {f.file_id for f in selected}
    by_id = {f.file_id: f for f in selected}

    dependents: dict[str, list[str]] = {f.file_id: [] for f in selected}
    in_degree: dict[str, int] = {f.file_id: 0 for f in selected}
    for f in selected:
        for dep_id in f.dependency_file_ids:
            if dep_id in selected_ids and dep_id != f.file_id:
                dependents[dep_id].append(f.file_id)
                in_degree[f.file_id] += 1

    # Process in original (criticality) order among ties, for determinism.
    ready = [f.file_id for f in selected if in_degree[f.file_id] == 0]
    ordered_ids: list[str] = []
    while ready:
        current = ready.pop(0)
        ordered_ids.append(current)
        for dependent_id in dependents[current]:
            in_degree[dependent_id] -= 1
            if in_degree[dependent_id] == 0:
                ready.append(dependent_id)

    if len(ordered_ids) < len(selected):
        remaining = [f.file_id for f in selected if f.file_id not in ordered_ids]
        ordered_ids.extend(remaining)

    return [by_id[fid] for fid in ordered_ids]


def _estimate_minutes(*, total_complexity: int, module_type: str) -> int:
    overhead = MODULE_OVERHEAD_MINUTES.get(module_type, 5)
    return max(MIN_ESTIMATED_MINUTES, round(total_complexity * MINUTES_PER_LOC) + overhead)


def build_modules(
    *, candidates: list[CandidateFile], role: str, experience_level: str
) -> list[GeneratedModule]:
    """Pure function (no I/O): selects, orders, and sizes learning modules
    from already-fetched candidate files. Kept separate from the Neo4j query
    in fetch_candidate_files so the selection/ordering/estimation logic is
    unit-testable against synthetic data, without a live database."""
    target_count = _target_module_count(role=role, experience_level=experience_level)
    intro_doc_count = _INTRO_DOC_MODULE_COUNT.get(experience_level, 0)

    selected = candidates[:target_count]
    ordered = _topological_order(selected)

    index_by_file_id = {f.file_id: i + intro_doc_count for i, f in enumerate(ordered)}

    modules: list[GeneratedModule] = []
    for i in range(intro_doc_count):
        modules.append(
            GeneratedModule(
                title="Get oriented" if i == 0 else "Understand the architecture",
                description=(
                    "Read the repository's README and skim its top-level structure "
                    "before diving into individual files."
                    if i == 0
                    else "Review how the major modules relate before going file-by-file."
                ),
                type="doc",
                target_entity_ids=[],
                order=i,
                prerequisite_indices=list(range(i)),
                estimated_minutes=_estimate_minutes(total_complexity=0, module_type="doc"),
            )
        )

    for i, f in enumerate(ordered):
        prereq_indices = [
            index_by_file_id[dep_id]
            for dep_id in f.dependency_file_ids
            if dep_id in index_by_file_id and index_by_file_id[dep_id] != i + intro_doc_count
        ]
        modules.append(
            GeneratedModule(
                title=f.file_path,
                description=f"Understand {f.component_count} component(s) defined in {f.file_path}.",
                type="code_area",
                target_entity_ids=[f.file_id],
                order=i + intro_doc_count,
                prerequisite_indices=prereq_indices,
                estimated_minutes=_estimate_minutes(
                    total_complexity=f.total_complexity, module_type="code_area"
                ),
            )
        )

    return modules
