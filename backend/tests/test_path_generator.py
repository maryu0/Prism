from app.modules.learning_paths.path_generator import CandidateFile, build_modules


def test_build_modules_orders_by_dependency():
    # b depends on a, c depends on b — a must come before b before c.
    candidates = [
        CandidateFile(
            file_id="c", file_path="c.py", component_count=1, total_complexity=10,
            incoming_dependency_count=0, dependency_file_ids=["b"],
        ),
        CandidateFile(
            file_id="b", file_path="b.py", component_count=1, total_complexity=10,
            incoming_dependency_count=1, dependency_file_ids=["a"],
        ),
        CandidateFile(
            file_id="a", file_path="a.py", component_count=1, total_complexity=10,
            incoming_dependency_count=2, dependency_file_ids=[],
        ),
    ]

    modules = build_modules(candidates=candidates, role="developer", experience_level="senior")

    order_by_file_id = {m.target_entity_ids[0]: m.order for m in modules if m.target_entity_ids}
    assert order_by_file_id["a"] < order_by_file_id["b"] < order_by_file_id["c"]


def test_build_modules_prerequisites_map_to_dependency_edges():
    candidates = [
        CandidateFile(
            file_id="b", file_path="b.py", component_count=1, total_complexity=10,
            incoming_dependency_count=0, dependency_file_ids=["a"],
        ),
        CandidateFile(
            file_id="a", file_path="a.py", component_count=1, total_complexity=10,
            incoming_dependency_count=1, dependency_file_ids=[],
        ),
    ]

    modules = build_modules(candidates=candidates, role="developer", experience_level="senior")

    module_a = next(m for m in modules if m.target_entity_ids == ["a"])
    module_b = next(m for m in modules if m.target_entity_ids == ["b"])
    assert module_a.prerequisite_indices == []
    assert module_a.order in module_b.prerequisite_indices


def test_build_modules_breaks_cycles_deterministically():
    # a imports b, b imports a — a genuine cycle. Generation must not hang or crash.
    candidates = [
        CandidateFile(
            file_id="a", file_path="a.py", component_count=1, total_complexity=10,
            incoming_dependency_count=1, dependency_file_ids=["b"],
        ),
        CandidateFile(
            file_id="b", file_path="b.py", component_count=1, total_complexity=10,
            incoming_dependency_count=1, dependency_file_ids=["a"],
        ),
    ]

    modules = build_modules(candidates=candidates, role="developer", experience_level="senior")

    assert len(modules) == 2
    assert {m.target_entity_ids[0] for m in modules} == {"a", "b"}


def test_build_modules_respects_experience_level_module_count():
    candidates = [
        CandidateFile(
            file_id=str(i), file_path=f"file{i}.py", component_count=1, total_complexity=10,
            incoming_dependency_count=0, dependency_file_ids=[],
        )
        for i in range(20)
    ]

    junior_modules = build_modules(candidates=candidates, role="developer", experience_level="junior")
    senior_modules = build_modules(candidates=candidates, role="developer", experience_level="senior")

    junior_code_modules = [m for m in junior_modules if m.type == "code_area"]
    senior_code_modules = [m for m in senior_modules if m.type == "code_area"]
    assert len(junior_code_modules) > len(senior_code_modules)


def test_build_modules_senior_role_reduces_count_further():
    candidates = [
        CandidateFile(
            file_id=str(i), file_path=f"file{i}.py", component_count=1, total_complexity=10,
            incoming_dependency_count=0, dependency_file_ids=[],
        )
        for i in range(20)
    ]

    developer_modules = build_modules(candidates=candidates, role="developer", experience_level="mid")
    senior_role_modules = build_modules(candidates=candidates, role="senior", experience_level="mid")

    assert len(senior_role_modules) < len(developer_modules)


def test_build_modules_junior_gets_intro_doc_modules():
    candidates = [
        CandidateFile(
            file_id="a", file_path="a.py", component_count=1, total_complexity=10,
            incoming_dependency_count=0, dependency_file_ids=[],
        )
    ]

    junior_modules = build_modules(candidates=candidates, role="developer", experience_level="junior")
    senior_modules = build_modules(candidates=candidates, role="developer", experience_level="senior")

    assert any(m.type == "doc" for m in junior_modules)
    assert not any(m.type == "doc" for m in senior_modules)


def test_estimated_minutes_scales_with_complexity_and_has_floor():
    small = CandidateFile(
        file_id="a", file_path="a.py", component_count=1, total_complexity=2,
        incoming_dependency_count=0, dependency_file_ids=[],
    )
    large = CandidateFile(
        file_id="b", file_path="b.py", component_count=1, total_complexity=200,
        incoming_dependency_count=0, dependency_file_ids=[],
    )

    modules = build_modules(candidates=[small, large], role="developer", experience_level="senior")

    module_small = next(m for m in modules if m.target_entity_ids == ["a"])
    module_large = next(m for m in modules if m.target_entity_ids == ["b"])
    assert module_small.estimated_minutes >= 10  # floor applies even for tiny files
    assert module_large.estimated_minutes > module_small.estimated_minutes
