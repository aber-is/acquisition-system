"""Normalized values and extraction provenance.

Information used by deterministic hard filters must retain more than the
normalized value alone: it must also record whether the value is known,
unknown or conflicting, the supporting source text or metadata, and how it was
extracted. :class:`NormalizedValue` carries all four. Purely descriptive fields
may hold plain values instead.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Self

from pydantic import Field, model_validator

from .base import Confidence, DomainModel, NonEmptyStr
from .enums import ExtractionMethod, ValueState


class ExtractionProvenance(DomainModel):
    """How and by what a value was extracted."""

    method: ExtractionMethod = ExtractionMethod.unknown
    """The kind of extraction that produced the value."""

    extractor: NonEmptyStr | None = None
    """Name of the rule, parser or model, including a version where available."""

    extracted_at: datetime | None = None
    """When the extraction ran."""

    confidence: Confidence | None = None
    """Reported confidence, where the extractor provides one."""

    notes: NonEmptyStr | None = None
    """Anything else needed to debug the extraction later."""


class NormalizedValue[T](DomainModel):
    """A value that normalization either determined, could not determine, or found in conflict.

    ``state`` is authoritative: ``value`` is set only when the state is
    ``known``, and ``candidates`` is populated only when two or more
    incompatible values were observed. Callers must therefore treat a missing
    value as unknown and never as satisfied.
    """

    state: ValueState = ValueState.unknown
    """Whether the value is known, unknown or conflicting."""

    value: T | None = None
    """The normalized value, present only when ``state`` is ``known``."""

    candidates: tuple[T, ...] = ()
    """The incompatible values observed, present only when ``state`` is ``conflicting``."""

    source_text: NonEmptyStr | None = None
    """The posting text that supports the value."""

    source_field: NonEmptyStr | None = None
    """The source metadata field that supports the value."""

    extraction: ExtractionProvenance = Field(default_factory=ExtractionProvenance)
    """How the value was obtained."""

    @model_validator(mode="after")
    def _check_state_consistency(self) -> Self:
        if self.state is ValueState.known and self.value is None:
            raise ValueError("a known normalized value must carry a value")
        if self.state is not ValueState.known and self.value is not None:
            raise ValueError("only a known normalized value may carry a value")
        if self.state is ValueState.conflicting and len(self.candidates) < 2:
            raise ValueError("a conflicting normalized value must retain at least two candidates")
        if self.state is not ValueState.conflicting and self.candidates:
            raise ValueError("only a conflicting normalized value may carry candidates")
        return self

    @property
    def is_known(self) -> bool:
        """Whether a single normalized value could be determined."""
        return self.state is ValueState.known

    @classmethod
    def known(cls, value: T, **support: Any) -> Self:
        """Build a known value, for example ``NormalizedValue[bool].known(True)``."""
        return cls(state=ValueState.known, value=value, **support)

    @classmethod
    def unknown(cls, **support: Any) -> Self:
        """Build an unknown value, optionally retaining the source text that was inconclusive."""
        return cls(state=ValueState.unknown, **support)

    @classmethod
    def conflicting(cls, *candidates: T, **support: Any) -> Self:
        """Build a conflicting value from the incompatible candidates that were observed."""
        return cls(state=ValueState.conflicting, candidates=candidates, **support)
