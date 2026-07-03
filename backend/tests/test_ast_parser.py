from pathlib import Path

from app.modules.ingestion.ast_parser import parse_file


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
