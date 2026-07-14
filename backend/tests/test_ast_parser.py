from pathlib import Path

from app.modules.ingestion.ast_parser import ParsedFile, parse_file, resolve_imports


def test_parses_python_classes_functions_and_imports(tmp_path: Path):
    source = """
import os
from collections import OrderedDict

class Foo:
    def bar(self):
        pass

def baz():
    return 1
"""
    file_path = tmp_path / "sample.py"
    file_path.write_text(source)

    parsed = parse_file(file_path, "sample.py")

    assert parsed.error is None
    assert parsed.language == "python"
    names_and_types = {(c.name, c.type) for c in parsed.components}
    assert ("Foo", "class") in names_and_types
    assert ("bar", "function") in names_and_types
    assert ("baz", "function") in names_and_types
    assert any("import os" in i for i in parsed.imports)
    assert any("OrderedDict" in i for i in parsed.imports)


def test_parses_javascript_classes_and_functions(tmp_path: Path):
    source = """
import React from 'react';

class Widget {
  render() {
    return null;
  }
}

function helper() {
  return 42;
}
"""
    file_path = tmp_path / "sample.js"
    file_path.write_text(source)

    parsed = parse_file(file_path, "sample.js")

    assert parsed.error is None
    assert parsed.language == "javascript"
    names_and_types = {(c.name, c.type) for c in parsed.components}
    assert ("Widget", "class") in names_and_types
    assert ("render", "function") in names_and_types
    assert ("helper", "function") in names_and_types
    assert any("react" in i for i in parsed.imports)


def test_parses_typescript(tmp_path: Path):
    source = """
export function add(a: number, b: number): number {
  return a + b;
}
"""
    file_path = tmp_path / "sample.ts"
    file_path.write_text(source)

    parsed = parse_file(file_path, "sample.ts")

    assert parsed.error is None
    assert parsed.language == "typescript"
    assert any(c.name == "add" and c.type == "function" for c in parsed.components)


def test_unsupported_extension_is_flagged_not_crashed(tmp_path: Path):
    file_path = tmp_path / "sample.rb"
    file_path.write_text("def hello; end")

    parsed = parse_file(file_path, "sample.rb")

    assert parsed.error == "Unsupported file extension"
    assert parsed.components == []


def test_binary_file_does_not_crash_the_parser(tmp_path: Path):
    file_path = tmp_path / "sample.py"
    file_path.write_bytes(b"\xff\xfe\x00\x01binary-garbage-not-utf8\x80\x81")

    parsed = parse_file(file_path, "sample.py")

    # tree-sitter parses arbitrary bytes without raising (it has no concept of
    # "invalid" source, it just produces a tree full of ERROR nodes) — the
    # real requirement is just that this never throws and always returns a
    # ParsedFile, which the ingestion pipeline can then reason about.
    assert parsed.file_path == "sample.py"


def test_resolve_imports_python_absolute():
    files = [
        ParsedFile(
            file_path="app/main.py",
            language="python",
            imports=["from app.core import config"],
        )
    ]
    all_paths = {"app/main.py", "app/core.py"}

    result = resolve_imports(files, all_paths)

    assert result == {"app/main.py": ["app/core.py"]}


def test_resolve_imports_python_relative_same_package():
    files = [
        ParsedFile(
            file_path="app/modules/auth/router.py",
            language="python",
            imports=["from . import service"],
        )
    ]
    all_paths = {"app/modules/auth/router.py", "app/modules/auth/service.py"}

    result = resolve_imports(files, all_paths)

    assert result == {"app/modules/auth/router.py": ["app/modules/auth/service.py"]}


def test_resolve_imports_python_relative_parent_package():
    # From app/modules/auth/router.py (package app.modules.auth), one dot is
    # the current package (app.modules.auth), so two dots is its parent
    # (app.modules) — "from ..core import database" resolves the *module*
    # `core` relative to app.modules, i.e. app/modules/core.py.
    files = [
        ParsedFile(
            file_path="app/modules/auth/router.py",
            language="python",
            imports=["from ..core import database"],
        )
    ]
    all_paths = {"app/modules/auth/router.py", "app/modules/core.py"}

    result = resolve_imports(files, all_paths)

    assert result == {"app/modules/auth/router.py": ["app/modules/core.py"]}


def test_resolve_imports_python_absolute_with_non_root_package_root():
    # Real-world layout: the Python package root is backend/, not the repo
    # root — "from app.core.config import ..." must resolve relative to
    # backend/, not be assumed relative to the repo root.
    files = [
        ParsedFile(
            file_path="backend/app/main.py",
            language="python",
            imports=["from app.core.config import get_settings"],
        )
    ]
    all_paths = {"backend/app/main.py", "backend/app/core/config.py"}

    result = resolve_imports(files, all_paths)

    assert result == {"backend/app/main.py": ["backend/app/core/config.py"]}


def test_resolve_imports_python_package_init():
    files = [
        ParsedFile(
            file_path="app/main.py",
            language="python",
            imports=["import app.modules"],
        )
    ]
    all_paths = {"app/main.py", "app/modules/__init__.py"}

    result = resolve_imports(files, all_paths)

    assert result == {"app/main.py": ["app/modules/__init__.py"]}


def test_resolve_imports_drops_external_packages():
    files = [
        ParsedFile(
            file_path="app/main.py",
            language="python",
            imports=["import os", "from collections import OrderedDict"],
        )
    ]
    all_paths = {"app/main.py"}

    result = resolve_imports(files, all_paths)

    assert result == {}


def test_resolve_imports_js_relative():
    files = [
        ParsedFile(
            file_path="src/pages/LoginPage.tsx",
            language="tsx",
            imports=["import { login } from '../lib/endpoints'"],
        )
    ]
    all_paths = {"src/pages/LoginPage.tsx", "src/lib/endpoints.ts"}

    result = resolve_imports(files, all_paths)

    assert result == {"src/pages/LoginPage.tsx": ["src/lib/endpoints.ts"]}


def test_resolve_imports_js_drops_bare_specifier():
    files = [
        ParsedFile(
            file_path="src/App.tsx",
            language="tsx",
            imports=["import React from 'react'"],
        )
    ]
    all_paths = {"src/App.tsx"}

    result = resolve_imports(files, all_paths)

    assert result == {}
