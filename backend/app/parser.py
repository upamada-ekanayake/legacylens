import ast
import posixpath
import re
from dataclasses import dataclass

from .graph_engine import assign_risk_levels, find_cycles
from .models import CodeEdge, CodeNode, CycleInfo

PY_EXTENSIONS = (".py",)
JS_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx")
SUPPORTED_EXTENSIONS = PY_EXTENSIONS + JS_EXTENSIONS

_JS_IMPORT_PATTERNS = [
    re.compile(r"""\bimport\s+(?:[\w*${}\s,]+?\s+from\s+)?['"]([^'"]+)['"]"""),
    re.compile(r"""\bexport\s+[\w*${}\s,]+?\s+from\s+['"]([^'"]+)['"]"""),
    re.compile(r"""\brequire\(\s*['"]([^'"]+)['"]\s*\)"""),
    re.compile(r"""\bimport\(\s*['"]([^'"]+)['"]\s*\)"""),
]


@dataclass(frozen=True)
class PyImport:
    module: str  # dotted name without leading dots
    level: int  # number of leading dots (0 = absolute)
    names: tuple[str, ...] = ()  # names in `from module import a, b`


def is_supported(path: str) -> bool:
    return path.lower().endswith(SUPPORTED_EXTENSIONS)


def parse_python(source: str) -> tuple[list[PyImport], str]:
    """Return (imports, first docstring line). Files with syntax errors yield no imports."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return [], ""
    imports: list[PyImport] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(PyImport(alias.name, 0) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(
                PyImport(node.module or "", node.level, tuple(a.name for a in node.names))
            )
    doc = ast.get_docstring(tree) or ""
    return imports, doc.strip().splitlines()[0] if doc.strip() else ""


def parse_js(source: str) -> list[str]:
    """Return raw import specifiers found in a JS/TS source file."""
    specs: list[str] = []
    for pattern in _JS_IMPORT_PATTERNS:
        specs.extend(pattern.findall(source))
    return specs


def _python_module_index(paths: list[str]) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Index dotted module names to file paths: exact (full path) and by suffix."""
    exact: dict[str, str] = {}
    suffix: dict[str, list[str]] = {}
    for path in paths:
        if not path.endswith(".py"):
            continue
        parts = path[:-3].split("/")
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if not parts:
            continue
        exact[".".join(parts)] = path
        for i in range(1, len(parts)):
            suffix.setdefault(".".join(parts[i:]), []).append(path)
    return exact, suffix


def _resolve_python(
    path: str,
    imp: PyImport,
    exact: dict[str, str],
    suffix: dict[str, list[str]],
) -> set[str]:
    candidates: list[str] = []
    if imp.level:
        base = posixpath.dirname(path).split("/") if "/" in path else []
        up = imp.level - 1
        if up > len(base):
            return set()
        base = base[: len(base) - up] if up else base
        prefix = ".".join(base)
        module = ".".join(p for p in (prefix, imp.module) if p)
        candidates.append(module)
        candidates.extend(".".join(p for p in (module, n) if p) for n in imp.names)
    else:
        candidates.append(imp.module)
        candidates.extend(f"{imp.module}.{n}" for n in imp.names)

    resolved: set[str] = set()
    for name in candidates:
        if not name:
            continue
        if name in exact:
            resolved.add(exact[name])
        elif not imp.level and len(suffix.get(name, [])) == 1:
            resolved.add(suffix[name][0])
    resolved.discard(path)
    return resolved


def _resolve_js(path: str, spec: str, known: set[str]) -> str | None:
    if not spec.startswith("."):
        return None  # external package or alias: never guess
    base = posixpath.normpath(posixpath.join(posixpath.dirname(path), spec))
    options = [base]
    options += [base + ext for ext in JS_EXTENSIONS]
    options += [posixpath.join(base, "index" + ext) for ext in JS_EXTENSIONS]
    # TS projects often import "./x.js" for an "x.ts" file.
    stem, ext = posixpath.splitext(base)
    if ext in (".js", ".jsx"):
        options += [stem + e for e in (".ts", ".tsx")]
    for option in options:
        if option in known and option != path:
            return option
    return None


def build_graph(files: dict[str, str]) -> tuple[list[CodeNode], list[CodeEdge], list[CycleInfo]]:
    """Build nodes/edges from {path: source}. Only edges between files that exist in `files` are emitted."""
    paths = sorted(p for p in files if is_supported(p))
    known = set(paths)
    exact, suffix = _python_module_index(paths)

    nodes: list[CodeNode] = []
    edge_set: dict[tuple[str, str], CodeEdge] = {}

    for path in paths:
        source = files[path]
        summary = ""
        targets: set[str] = set()
        if path.endswith(PY_EXTENSIONS):
            imports, summary = parse_python(source)
            for imp in imports:
                targets |= _resolve_python(path, imp, exact, suffix)
        else:
            for spec in parse_js(source):
                resolved = _resolve_js(path, spec, known)
                if resolved:
                    targets.add(resolved)
        nodes.append(
            CodeNode(id=path, label=posixpath.basename(path), kind="file", path=path, summary=summary)
        )
        for target in targets:
            edge_set[(path, target)] = CodeEdge(source=path, target=target, relation="imports")

    edges = [edge_set[k] for k in sorted(edge_set)]
    assign_risk_levels(nodes, edges)
    return nodes, edges, find_cycles(nodes, edges)
