"""Opportunities and the requirements they state."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal, Self

from pydantic import Field, HttpUrl, TypeAdapter, model_validator

from .base import DomainModel, NonEmptyStr, OpportunityId, Slug, SourceId
from .enums import (
    CommercialArrangement,
    OpportunityStatus,
    OpportunityType,
    RequirementCategory,
    RequirementImportance,
)
from .normalization import ExtractionProvenance, NormalizedValue
from .values import (
    CommercialTerms,
    GeoLocation,
    TravelRequirement,
    Workload,
    WorkLocationRequirement,
)


class Requirement(DomainModel):
    """Something an opportunity asks for.

    Only an explicit mandatory requirement that the source supports may
    directly cause deterministic rejection. Preferred, optional, unknown,
    ambiguous or conflicting requirements may affect matching but must not
    cause a hard rejection.
    """

    description: NonEmptyStr
    """The requirement in words."""

    category: RequirementCategory = RequirementCategory.other
    """What kind of thing is being asked for."""

    subject: Slug | None = None
    """The normalized subject, for example ``python`` or ``de``, when one could be determined."""

    importance: RequirementImportance = RequirementImportance.unknown
    """How strongly the source states the requirement."""

    source_text: NonEmptyStr | None = None
    """The posting text the requirement was read from."""

    source_field: NonEmptyStr | None = None
    """The source metadata field the requirement was read from."""

    extraction: ExtractionProvenance | None = None
    """How the requirement was extracted."""

    @property
    def is_explicit(self) -> bool:
        """Whether the requirement is backed by source text or source metadata."""
        return self.source_text is not None or self.source_field is not None

    @property
    def may_cause_rejection(self) -> bool:
        """Whether this requirement alone may justify a deterministic rejection."""
        return self.importance is RequirementImportance.mandatory and self.is_explicit


class Opportunity(DomainModel):
    """A potential piece of work.

    The original posting text and source URL are always retained so that the
    opportunity can be audited, rescored and reprocessed later without going
    back to the source.

    Fields used by deterministic hard filters are
    :class:`~acquisition.domain.normalization.NormalizedValue` wrappers, which
    keep the normalized value, whether it is known, unknown or conflicting, the
    supporting source text or metadata, and the extraction method.
    """

    id: OpportunityId
    """Stable identifier assigned during normalization."""

    opportunity_type: OpportunityType
    """What the client is primarily buying."""

    title: NonEmptyStr
    """Title of the posting."""

    client: NonEmptyStr | None = None
    """The client, where the posting names one."""

    source_id: SourceId
    """Identifier of the :class:`~acquisition.domain.source.Source` it came from."""

    source_url: HttpUrl
    """Link to the original posting."""

    original_text: NonEmptyStr
    """The posting text exactly as published. Never replaced by normalized output."""

    first_seen_date: date
    """When the opportunity was first observed."""

    last_seen_date: date
    """When the opportunity was last observed. Records observation only."""

    publication_date: date | None = None
    """When the source published it, if known."""

    application_deadline: date | None = None
    """When responses are due, if known."""

    status: NormalizedValue[OpportunityStatus] = Field(
        default_factory=NormalizedValue[OpportunityStatus].unknown
    )
    """Listing status. Disappearing from a source does not make an opportunity ``closed``."""

    location: NormalizedValue[GeoLocation] = Field(
        default_factory=NormalizedValue[GeoLocation].unknown
    )
    """Where the work is, as stated by the source."""

    work_location: NormalizedValue[WorkLocationRequirement] = Field(
        default_factory=NormalizedValue[WorkLocationRequirement].unknown
    )
    """Whether the work is on site, hybrid or remote. Decides viability with ``location``."""

    workload: NormalizedValue[Workload] = Field(
        default_factory=NormalizedValue[Workload].unknown
    )
    """How much capacity is asked for."""

    requirements: tuple[Requirement, ...] = ()
    """What the opportunity asks for."""

    formal_tender: bool = False
    """Whether this is a formal tender. Keeps tenders identifiable without a separate type."""

    commercial_arrangements: NormalizedValue[tuple[CommercialArrangement, ...]] = Field(
        default_factory=NormalizedValue[tuple[CommercialArrangement, ...]].unknown
    )
    """The contracting or pricing arrangements the opportunity allows."""

    commercial_terms: CommercialTerms | None = None
    """Published rates, budget, payment terms and contract value."""

    travel: TravelRequirement | None = None
    """Travel the opportunity requires, if any."""

    source_metadata: dict[str, str] = Field(default_factory=dict)
    """Raw source fields worth keeping, so reports need not reprocess the posting."""

    @model_validator(mode="after")
    def _check_observation_dates(self) -> Self:
        if self.last_seen_date < self.first_seen_date:
            raise ValueError("an opportunity cannot be last seen before it was first seen")
        return self

    @property
    def mandatory_requirements(self) -> tuple[Requirement, ...]:
        """The requirements that may justify a deterministic rejection."""
        return tuple(item for item in self.requirements if item.may_cause_rejection)


class IndividualOpportunity(Opportunity):
    """The client primarily wants a particular person or specialist capacity.

    Examples are a freelance developer, an AI consultant, a technical project
    manager, an infrastructure engineer or a part-time external specialist.

    The work may still be contracted and invoiced through Aber Industrial
    Solutions Ltd: this type says nothing about the contracting arrangement,
    which is recorded in ``commercial_arrangements``.
    """

    opportunity_type: Literal[OpportunityType.individual_opportunity] = (
        OpportunityType.individual_opportunity
    )


class CompanyOpportunity(Opportunity):
    """The client is primarily buying an outcome or deliverable from the company.

    Examples are building an internal AI automation system, modernizing an
    industrial application, implementing monitoring and backup infrastructure,
    migrating a legacy system or delivering a technical assessment.

    One or several employees may be involved; the defining characteristic is
    that Aber Industrial Solutions Ltd is responsible for the agreed result.
    """

    opportunity_type: Literal[OpportunityType.company_opportunity] = (
        OpportunityType.company_opportunity
    )


AnyOpportunity = Annotated[
    IndividualOpportunity | CompanyOpportunity,
    Field(discriminator="opportunity_type"),
]
"""Either concrete opportunity type, discriminated by ``opportunity_type``."""

opportunity_adapter: TypeAdapter[AnyOpportunity] = TypeAdapter(AnyOpportunity)
"""Validates and serializes an opportunity of either type."""
