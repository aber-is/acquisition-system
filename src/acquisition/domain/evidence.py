"""The evidence library.

Evidence supports claims made by a person or company profile. One project is
frequently evidence for both a person and the company, so an evidence item
belongs to neither profile: it is written down once in the library, and profiles
hold references into it.

A reference states the involvement. A person claiming a capability and citing an
evidence item is the explicit statement that this person's work on it
demonstrates that capability, and
:class:`~acquisition.domain.values.EvidenceRef` carries a note describing what
they contributed.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, HttpUrl, model_validator

from .base import DomainModel, EvidenceId, NonEmptyStr, Slug
from .normalization import ExtractionProvenance
from .values import DatePeriod, EvidenceRef


class Evidence(DomainModel):
    """Why a skill, capability, credential or experience claim is considered demonstrated.

    Evidence is typically a project, customer engagement, production system,
    certification project, technology implementation or documented
    responsibility.
    """

    id: EvidenceId
    """Stable identifier, cited by :class:`~acquisition.domain.values.EvidenceRef`."""

    description: NonEmptyStr
    """What was done, in enough detail to judge the claims it supports."""

    capabilities: tuple[Slug, ...] = ()
    """The normalized claims or capabilities this evidence demonstrates."""

    source: NonEmptyStr | None = None
    """Where the evidence comes from, for example a work summary or a project record."""

    url: HttpUrl | None = None
    """Link to the original material, where one exists."""

    period: DatePeriod | None = None
    """When the work happened, if known."""

    recorded_at: datetime | None = None
    """When this evidence item was written down."""

    extraction: ExtractionProvenance | None = None
    """How the evidence item was produced, when it was not authored by hand."""

    @model_validator(mode="after")
    def _check_provenance(self) -> Self:
        if self.source is None and self.url is None and self.extraction is None:
            raise ValueError("evidence must retain a source, a URL or its extraction provenance")
        return self


class EvidenceLibrary(DomainModel):
    """Every evidence item, held once."""

    items: tuple[Evidence, ...] = ()
    """The evidence items, each with a distinct identifier."""

    @model_validator(mode="after")
    def _check_unique_ids(self) -> Self:
        seen: set[str] = set()
        for item in self.items:
            if item.id in seen:
                raise ValueError(f"duplicate evidence id {item.id!r}")
            seen.add(item.id)
        return self

    @property
    def by_id(self) -> dict[str, Evidence]:
        """The items, indexed by identifier."""
        return {item.id: item for item in self.items}

    def resolve(self, reference: EvidenceRef) -> Evidence:
        """Return the referenced item, or raise :class:`KeyError` if the library lacks it."""
        try:
            return self.by_id[reference.evidence_id]
        except KeyError:
            raise KeyError(f"unknown evidence {reference.evidence_id!r}") from None

    def unresolved(self, value: Any) -> tuple[EvidenceRef, ...]:
        """Every reference reachable from ``value`` that this library cannot resolve."""
        known = self.by_id
        return tuple(
            reference
            for reference in iter_evidence_refs(value)
            if reference.evidence_id not in known
        )


def iter_evidence_refs(value: Any) -> Iterator[EvidenceRef]:
    """Yield every :class:`EvidenceRef` reachable from ``value``."""
    if isinstance(value, EvidenceRef):
        yield value
    elif isinstance(value, BaseModel):
        for field_name in type(value).model_fields:
            yield from iter_evidence_refs(getattr(value, field_name))
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from iter_evidence_refs(item)
    elif isinstance(value, list | tuple | set | frozenset):
        for item in value:
            yield from iter_evidence_refs(item)
