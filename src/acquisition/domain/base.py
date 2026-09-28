"""Shared base class, identifier types and constrained scalars for the domain layer."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class DomainModel(BaseModel):
    """Base class for every domain model.

    Domain objects are immutable, validated value objects: they reject unknown
    fields so that a renamed or misspelled attribute fails loudly instead of
    being silently dropped, and they are frozen so that pure functions can pass
    them around without defensive copying.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        validate_default=True,
        use_attribute_docstrings=True,
    )


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
"""Human-readable text that must carry at least one non-whitespace character."""

Slug = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        pattern=r"^[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*$",
    ),
]
"""A stable, lowercase machine identifier such as ``salomon`` or ``nixos``."""

# Identifier aliases. They share one representation but are named after the
# concept they identify so that signatures stay readable.
PersonId = Slug
CompanyId = Slug
OpportunityId = Slug
EvidenceId = Slug
SourceId = Slug
CredentialId = Slug
ProjectId = Slug

CountryCode = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_upper=True, pattern=r"^[A-Za-z]{2}$"),
]
"""ISO 3166-1 alpha-2 country code, for example ``CH``."""

LanguageCode = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_lower=True, pattern=r"^[A-Za-z]{2,3}$"),
]
"""ISO 639 language code, for example ``de`` or ``en``."""

CurrencyCode = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_upper=True, pattern=r"^[A-Za-z]{3}$"),
]
"""ISO 4217 currency code, for example ``CHF``."""

Percentage = Annotated[float, Field(ge=0, le=100)]
"""A share of a whole, expressed from 0 to 100."""

HoursPerWeek = Annotated[float, Field(ge=0, le=168)]
"""Weekly hours, bounded by the number of hours in a week."""

Confidence = Annotated[float, Field(ge=0, le=1)]
"""Confidence in an extracted value, from 0 (none) to 1 (certain)."""

Score = Annotated[float, Field(ge=0, le=100)]
"""A match score on the fixed 0-100 scale used across the system."""
