import re
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


_PY_RELATIVE_IMPORT_RE = re.compile(r"^from\s+(\.+)(\w[\w.]*)?\s+import\s+(.+)$")
_PY_ABSOLUTE_IMPORT_RE = re.compile(r"^import\s+([\w.]+)|^from\s+([\w.]+)\s+import\b")
_JS_IMPORT_RE = re.compile(r"""from\s+['"]([^'"]+)['"]""")

_JS_RESOLUTION_SUFFIXES = (".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.tsx", "/index.js")


def _resolve_python_import(raw_import: str, importing_file: str) -> tuple[list[str], bool]:
    """Returns (candidates, is_anchored). Anchored candidates are already a
    full repo-relative path (from a relative import, unambiguous). Absolute
    imports (`import a.b.c`) are NOT anchored — the module path is relative
    to whatever the project's package root is (e.g. `backend/`, `src/`),
    which isn't knowable from the import statement alone, so the caller
    must try it against multiple candidate roots."""
    relative_match = _PY_RELATIVE_IMPORT_RE.match(raw_import)
    if relative_match:
        dots, module_tail, imported_names = relative_match.groups()
        # One dot means "this package" (the importing file's own directory);
        # each extra dot walks up one more directory level.
        base = Path(importing_file).parent
        for _ in range(len(dots) - 1):
            base = base.parent
        if module_tail:
            # "from .foo import bar" — bar is an attribute of module foo, not
            # a submodule itself, so the target is just foo.
            return [(base / module_tail.replace(".", "/")).as_posix()], True
        # "from . import service[, other]" — each imported name here is a
        # submodule of the current package.
        names = [n.strip().split(" as ")[0] for n in imported_names.split(",")]
        return [(base / name).as_posix() for name in names if name], True

    absolute_match = _PY_ABSOLUTE_IMPORT_RE.match(raw_import)
    if not absolute_match:
        return [], False
    module = absolute_match.group(1) or absolute_match.group(2)
    if not module:
        return [], False
    return [module.replace(".", "/")], False


def _resolve_js_import(raw_import: str, importing_file: str) -> str | None:
    match = _JS_IMPORT_RE.search(raw_import)
    if not match:
        return None
    spec = match.group(1)
    if not spec.startswith(".") and not spec.startswith("/"):
        return None  # bare specifier -> external package, not an in-repo file

    base = Path(importing_file).parent
    candidate = (base / spec).as_posix()
    # Collapse "a/b/../c" -> "a/c" style segments produced by "../" specs.
    parts: list[str] = []
    for part in candidate.split("/"):
        if part == "..":
            if parts:
                parts.pop()
        elif part != ".":
            parts.append(part)
    return "/".join(parts)


def resolve_imports(
    parsed_files: list[ParsedFile], all_relative_paths: set[str]
) -> dict[str, list[str]]:
    """Turns each file's raw import strings into resolved in-repo target file
    paths, dropping anything that doesn't match a real file in the repo
    (external packages like `os` or `react`, or unresolvable specifiers).
    File-level only — no attempt at function/call-level resolution, since
    that would require real symbol binding per language, not just path
    matching."""
    result: dict[str, list[str]] = {}

    for parsed_file in parsed_files:
        targets: list[str] = []
        for raw_import in parsed_file.imports:
            if parsed_file.language == "python":
                candidates, is_anchored = _resolve_python_import(
                    raw_import, parsed_file.file_path
                )
            elif parsed_file.language in ("javascript", "typescript", "tsx"):
                js_candidate = _resolve_js_import(raw_import, parsed_file.file_path)
                candidates = [js_candidate] if js_candidate is not None else []
                is_anchored = True
            else:
                candidates, is_anchored = [], True

            for candidate in candidates:
                if parsed_file.language == "python":
                    if is_anchored:
                        roots = [candidate]
                    else:
                        # Absolute import — the module path is relative to an
                        # unknown package root, so try it under every ancestor
                        # directory of the importing file (repo root, backend/,
                        # src/, etc.) rather than assuming repo-root-relative.
                        ancestors = [Path(parsed_file.file_path).parent]
                        while ancestors[-1] != Path("."):
                            ancestors.append(ancestors[-1].parent)
                        roots = [
                            (ancestor / candidate).as_posix() if str(ancestor) != "." else candidate
                            for ancestor in ancestors
                        ]

                    resolved = next(
                        (
                            p
                            for root in roots
                            for p in (f"{root}.py", f"{root}/__init__.py")
                            if p in all_relative_paths
                        ),
                        None,
                    )
                else:
                    resolved = next(
                        (
                            p
                            for p in (
                                candidate,
                                *(f"{candidate}{suf}" for suf in _JS_RESOLUTION_SUFFIXES),
                            )
                            if p in all_relative_paths
                        ),
                        None,
                    )

                if resolved is not None and resolved != parsed_file.file_path:
                    targets.append(resolved)

        if targets:
            result[parsed_file.file_path] = targets

    return result
