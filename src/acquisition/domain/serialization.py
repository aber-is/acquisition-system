"""JSON and YAML serialization for domain objects.

Serialization always goes through Pydantic's JSON mode, so YAML and JSON carry
exactly the same representation and both round-trip back into validated domain
objects.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, TypeAdapter


def to_jsonable(value: BaseModel) -> Any:
    """Convert a domain object into plain JSON-compatible data."""
    return value.model_dump(mode="json")


def to_json(value: BaseModel, *, indent: int | None = 2) -> str:
    """Serialize a domain object to JSON."""
    return json.dumps(to_jsonable(value), indent=indent, ensure_ascii=False)


def to_yaml(value: BaseModel) -> str:
    """Serialize a domain object to YAML, keeping the declared field order."""
    return yaml.safe_dump(
        to_jsonable(value),
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )


def from_jsonable[T](model_type: type[T] | Any, data: Any) -> T:
    """Validate plain data into a domain object.

    ``model_type`` may be a model class or an annotated union such as
    :data:`~acquisition.domain.opportunity.AnyOpportunity`.
    """
    return TypeAdapter(model_type).validate_python(data)


def from_json[T](model_type: type[T] | Any, text: str | bytes) -> T:
    """Validate JSON text into a domain object."""
    return from_jsonable(model_type, json.loads(text))


def from_yaml[T](model_type: type[T] | Any, text: str | bytes) -> T:
    """Validate YAML text into a domain object."""
    return from_jsonable(model_type, yaml.safe_load(text))


def read_yaml_file[T](model_type: type[T] | Any, path: Path | str) -> T:
    """Read and validate a YAML file into a domain object."""
    return from_yaml(model_type, Path(path).read_text(encoding="utf-8"))


def write_yaml_file(value: BaseModel, path: Path | str) -> None:
    """Write a domain object to a YAML file."""
    Path(path).write_text(to_yaml(value), encoding="utf-8")
