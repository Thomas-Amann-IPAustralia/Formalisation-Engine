"""JSON Schema generated from the models (NFR-MNT-01, NFR-INT-01).

NFR-MNT-01 says the Pydantic models are defined once and the JSON Schema is generated from
them; NFR-INT-01 says the IR schema and the contract schema are published per version. So
`schema/` is an output, never a source: it is written by `engine schema export` and committed,
and `--check` fails when it has drifted from the models.

Output is byte-deterministic — sorted keys, two-space indent, UTF-8, one trailing newline — so
that a diff on a generated file means a model changed and nothing else (NFR-DET-01).
"""

from __future__ import annotations

import difflib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

from engine.models.contract import CONTRACT_VERSION, ToolRequest, ToolResponse
from engine.models.ir import IR, IR_SCHEMA_VERSION

#: Where the published schemas resolve from (NFR-INT-01, "IDs convertible to IRIs").
BASE_IRI: Final = "https://formalisation.engine/schema/"

#: The draft the generated documents conform to.
JSON_SCHEMA_DIALECT: Final = "https://json-schema.org/draft/2020-12/schema"


def _document(
    model: type[IR] | type[ToolRequest] | type[ToolResponse], relative: str, mode: str, title: str
) -> str:
    """One schema document, rendered deterministically."""
    schema: dict[str, Any] = model.model_json_schema(
        mode=mode,  # type: ignore[arg-type]
        ref_template="#/$defs/{model}",
    )
    schema["$schema"] = JSON_SCHEMA_DIALECT
    schema["$id"] = f"{BASE_IRI}{relative}"
    schema["title"] = title
    return json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def generate() -> Mapping[str, str]:
    """Every published schema, keyed by its path relative to `schema/`.

    The IR and the response are rendered in serialisation mode, because `overall` is a computed
    field: a consumer reading a stored IR or a response sees it, and a validation-mode schema
    would leave it out. The request is rendered in validation mode, because that is what a
    caller is constructing.
    """
    ir_path = f"ir/{IR_SCHEMA_VERSION}/ir.schema.json"
    request_path = f"contract/{CONTRACT_VERSION}/request.schema.json"
    response_path = f"contract/{CONTRACT_VERSION}/response.schema.json"
    return {
        ir_path: _document(IR, ir_path, "serialization", "Formalisation Engine IR"),
        request_path: _document(
            ToolRequest, request_path, "validation", "Formalisation Engine tool request"
        ),
        response_path: _document(
            ToolResponse, response_path, "serialization", "Formalisation Engine tool response"
        ),
    }


def write(root: Path) -> tuple[str, ...]:
    """Write every schema under `root`, atomically. Returns the paths written."""
    written: list[str] = []
    for relative, content in sorted(generate().items()):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(target)
        written.append(relative)
    return tuple(written)


def drift(root: Path) -> tuple[str, ...]:
    """A unified diff per schema that is missing or out of date under `root`.

    Empty means the committed schema matches the models.
    """
    reports: list[str] = []
    for relative, expected in sorted(generate().items()):
        target = root / relative
        actual = target.read_text(encoding="utf-8") if target.exists() else ""
        if actual == expected:
            continue
        diff = difflib.unified_diff(
            actual.splitlines(keepends=True),
            expected.splitlines(keepends=True),
            fromfile=f"{relative} (committed)",
            tofile=f"{relative} (from the models)",
            n=2,
        )
        reports.append(f"{relative}\n{''.join(diff)}")
    return tuple(reports)
