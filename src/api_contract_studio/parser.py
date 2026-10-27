from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple
import yaml


class SpecParseError(Exception):
    """Raised when an OpenAPI document cannot be read or parsed."""


class SpecRefError(Exception):
    """Raised when reference resolution fails or encounters forbidden targets."""


MAX_SPEC_SIZE_BYTES = 10 * 1024 * 1024  # 10MB limit


def parse_spec_content(content: str, source_name: str = "spec") -> Dict[str, Any]:
    """Parse raw YAML or JSON string safely into a dict."""
    if len(content.encode("utf-8")) > MAX_SPEC_SIZE_BYTES:
        raise SpecParseError(f"Document {source_name} exceeds maximum allowed size of 10MB.")

    trimmed = content.strip()
    if not trimmed:
        raise SpecParseError(f"Document {source_name} is empty.")

    # Try JSON first if it looks like JSON
    if trimmed.startswith("{") or trimmed.startswith("["):
        try:
            parsed = json.loads(trimmed)
            if isinstance(parsed, dict):
                return parsed
            raise SpecParseError(f"Root of {source_name} must be a JSON object, got {type(parsed).__name__}")
        except json.JSONDecodeError:
            pass  # Fallback to YAML

    try:
        parsed = yaml.safe_load(trimmed)
        if not isinstance(parsed, dict):
            raise SpecParseError(f"Root of {source_name} must be a dictionary/object, got {type(parsed).__name__}")
        return parsed
    except yaml.YAMLError as exc:
        raise SpecParseError(f"Failed to parse {source_name} as YAML/JSON: {exc}") from exc


def load_spec_file(file_path: str | Path) -> Dict[str, Any]:
    """Load and parse specification from local filesystem."""
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if p.stat().st_size > MAX_SPEC_SIZE_BYTES:
        raise SpecParseError(f"File {file_path} exceeds maximum allowed size of 10MB.")
    content = p.read_text(encoding="utf-8")
    return parse_spec_content(content, source_name=p.name)


def resolve_local_ref(ref: str, root_doc: Dict[str, Any], seen_refs: Optional[Set[str]] = None) -> Any:
    """Resolve a local JSON Pointer ref (e.g. #/components/schemas/Pet).
    
    Prevents cyclic reference loops and rejects external/remote refs.
    """
    if seen_refs is None:
        seen_refs = set()

    if not ref.startswith("#/"):
        raise SpecRefError(f"External references are disabled for security: '{ref}'")

    if ref in seen_refs:
        # Detected cycle - return sentinel dict with $ref to break loop
        return {"type": "object", "x-circular-ref": ref}

    seen_refs.add(ref)
    tokens = ref[2:].split("/")
    current: Any = root_doc

    for token in tokens:
        # Decode JSON pointer escapes
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        else:
            raise SpecRefError(f"Reference target not found: '{ref}' (failed at segment '{token}')")

    if isinstance(current, dict) and "$ref" in current:
        return resolve_local_ref(current["$ref"], root_doc, seen_refs)

    return current


def dereference_spec(doc: Dict[str, Any], max_depth: int = 20) -> Dict[str, Any]:
    """Recursively resolves all local $ref pointers in a document up to max_depth."""
    def _walk(node: Any, depth: int, active_path: Set[str]) -> Any:
        if depth > max_depth:
            return node
        if isinstance(node, dict):
            if "$ref" in node and isinstance(node["$ref"], str):
                ref = node["$ref"]
                if ref in active_path:
                    return {"type": "object", "x-circular-ref": ref}
                try:
                    resolved = resolve_local_ref(ref, doc, active_path.copy())
                    # Merge properties if 3.1 allows sibling properties with $ref
                    if isinstance(resolved, dict):
                        merged = _walk(resolved, depth + 1, active_path | {ref})
                        for k, v in node.items():
                            if k != "$ref" and k not in merged:
                                merged[k] = _walk(v, depth + 1, active_path)
                        return merged
                    return resolved
                except SpecRefError:
                    return node  # Keep intact to be caught during validation

            return {k: _walk(v, depth + 1, active_path) for k, v in node.items()}
        elif isinstance(node, list):
            return [_walk(item, depth + 1, active_path) for item in node]
        return node

    return _walk(doc, 0, set())
