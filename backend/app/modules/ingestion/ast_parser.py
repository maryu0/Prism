from dataclasses import dataclass, field
from pathlib import Path

import tree_sitter
import tree_sitter_javascript
import tree_sitter_python
import tree_sitter_typescript

LANGUAGE_BY_EXTENSION = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
}

# Node type names differ between Python's grammar and the JS-family grammars,
# so each language needs its own query even though the concepts (function,
# class, import) are the same.
QUERIES = {
    "python": """
        (function_definition name: (identifier) @func.name) @func.def
        (class_definition name: (identifier) @class.name) @class.def
        (import_statement) @import
        (import_from_statement) @import
    """,
    "javascript": """
        (function_declaration name: (identifier) @func.name) @func.def
        (class_declaration name: (identifier) @class.name) @class.def
        (method_definition name: (property_identifier) @func.name) @func.def
        (import_statement) @import
    """,
    # TypeScript's grammar is a distinct grammar from JavaScript's, not just JS
    # plus extra syntax — despite the near-identical concepts, `class_declaration`'s
    # name field is a `type_identifier` node here, not `identifier` as in JS. Reusing
    # the JS query verbatim fails to even compile against the TS grammar.
    "typescript": """
        (function_declaration name: (identifier) @func.name) @func.def
        (class_declaration name: (type_identifier) @class.name) @class.def
        (method_definition name: (property_identifier) @func.name) @func.def
        (import_statement) @import
    """,
}
QUERIES["tsx"] = QUERIES["typescript"]

_LANGUAGE_CACHE: dict[str, tree_sitter.Language] = {}


def _get_language(language: str) -> tree_sitter.Language:
    if language not in _LANGUAGE_CACHE:
        if language == "python":
            capsule = tree_sitter_python.language()
        elif language == "javascript":
            capsule = tree_sitter_javascript.language()
        elif language == "typescript":
            capsule = tree_sitter_typescript.language_typescript()
        elif language == "tsx":
            capsule = tree_sitter_typescript.language_tsx()
        else:
            raise ValueError(f"Unsupported language: {language}")
        _LANGUAGE_CACHE[language] = tree_sitter.Language(capsule)
    return _LANGUAGE_CACHE[language]


@dataclass
class ParsedComponent:
    name: str
    type: str  # "class" | "function"
    file_path: str
    start_line: int
    end_line: int
    language: str


@dataclass
class ParsedFile:
    file_path: str
    language: str
    components: list[ParsedComponent] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    error: str | None = None


def parse_file(absolute_path: Path, relative_path: str) -> ParsedFile:
    language = LANGUAGE_BY_EXTENSION.get(absolute_path.suffix)
    if language is None:
        return ParsedFile(
            file_path=relative_path, language="unknown", error="Unsupported file extension"
        )

    try:
        source = absolute_path.read_bytes()
        ts_language = _get_language(language)
        parser = tree_sitter.Parser(ts_language)
        tree = parser.parse(source)

        query = tree_sitter.Query(ts_language, QUERIES[language])
        cursor = tree_sitter.QueryCursor(query)

        components: list[ParsedComponent] = []
        imports: list[str] = []

        for _pattern_index, match in cursor.matches(tree.root_node):
            if "func.def" in match:
                node = match["func.def"][0]
                name = match["func.name"][0]
                components.append(
                    ParsedComponent(
                        name=source[name.start_byte : name.end_byte].decode("utf-8"),
                        type="function",
                        file_path=relative_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        language=language,
                    )
                )
            elif "class.def" in match:
                node = match["class.def"][0]
                name = match["class.name"][0]
                components.append(
                    ParsedComponent(
                        name=source[name.start_byte : name.end_byte].decode("utf-8"),
                        type="class",
                        file_path=relative_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        language=language,
                    )
                )
            elif "import" in match:
                node = match["import"][0]
                imports.append(source[node.start_byte : node.end_byte].decode("utf-8").strip())

        return ParsedFile(
            file_path=relative_path, language=language, components=components, imports=imports
        )
    except (UnicodeDecodeError, OSError) as exc:
        # A single unparseable file (binary content, permissions issue, etc.)
        # must not fail the whole ingestion job — it's recorded and skipped.
        return ParsedFile(file_path=relative_path, language=language, error=str(exc))
