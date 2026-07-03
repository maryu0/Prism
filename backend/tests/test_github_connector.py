from pathlib import Path

from app.modules.ingestion.github_connector import (
    build_authenticated_url,
    discover_source_files,
)


def test_build_authenticated_url_embeds_token():
    url = build_authenticated_url("https://github.com/org/repo", "ghp_faketoken123")
    assert url == "https://ghp_faketoken123@github.com/org/repo"


def test_build_authenticated_url_without_token_is_unchanged():
    url = build_authenticated_url("https://github.com/org/repo", None)
    assert url == "https://github.com/org/repo"


def test_discover_source_files_filters_by_extension_and_ignores_junk_dirs(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / "src" / "app.ts").write_text("const x = 1;")
    (tmp_path / "src" / "styles.css").write_text("body {}")
    (tmp_path / "README.md").write_text("# hi")

    ignored_dir = tmp_path / "node_modules" / "some_pkg"
    ignored_dir.mkdir(parents=True)
    (ignored_dir / "index.js").write_text("module.exports = {};")

    found = discover_source_files(tmp_path)
    found_names = {p.name for p in found}

    assert found_names == {"main.py", "app.ts"}
