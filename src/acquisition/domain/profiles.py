"""Profiles of the people and the company that opportunities are matched against.

Profiles cite evidence but do not contain it. References are resolved against
the :class:`~acquisition.domain.evidence.EvidenceLibrary` held by a
:class:`~acquisition.domain.catalogue.ProfileCatalogue`, which is what validates
that every citation points at something real.
"""

from __future__ import annotations

from typing import Self

from pydantic import Field, HttpUrl, model_validator

from .base import (
    CompanyId,
    DomainModel,
    NonEmptyStr,
    PersonId,
    Slug,
)
from .enums import CommercialArrangement
from .values import (
    Availability,
    CommercialExpectations,
    ContractingEntity,
    Credential,
    EligibilityConstraint,
    EvidenceRef,
    GeographicScope,
    GeoLocation,
    LanguageSkill,
    ProjectReference,
    SubjectRef,
    Workload,
    WorkLocationPreference,
)


class EvidencedClaim(DomainModel):
    """A claim that is only made because evidence supports it.

    Claims are never inferred from vaguely related work: at least one evidence
    reference is required, and the reference's note is where the subject's own
    contribution is described.
    """

    subject: Slug
    """The normalized thing being claimed, for example ``nixos`` or ``water_treatment``."""

    label: NonEmptyStr | None = None
    """Human-readable name, where the normalized subject is not self-explanatory."""

    evidence: tuple[EvidenceRef, ...] = Field(min_length=1)
    """Evidence demonstrating the claim."""

    notes: NonEmptyStr | None = None
    """Scope or limits of the claim."""


class DemonstratedCapability(EvidencedClaim):
    """A skill, capability or technology that evidence demonstrates."""


class DomainExperience(EvidencedClaim):
    """An industry or domain that evidence demonstrates experience in."""


class PersonProfile(DomainModel):
    """One person who may be matched against individual freelance or consulting opportunities."""

    id: PersonId
    """Stable identifier, for example ``salomon``."""

    name: NonEmptyStr
    """The person's name."""

    availability: Availability = Field(default_factory=Availability)
    """Current availability, including known future changes."""

    maximum_workload: Workload | None = None
    """The most the person can take on."""

    preferred_workload: Workload | None = None
    """The workload the person would rather have."""

    location: GeoLocation | None = None
    """Where the person is based."""

    work_location_preference: WorkLocationPreference | None = None
    """Remote and on-site preferences."""

    languages: tuple[LanguageSkill, ...] = ()
    """Languages the person works in."""

    capabilities: tuple[DemonstratedCapability, ...] = ()
    """Demonstrated skills and capabilities, each citing evidence."""

    domains: tuple[DomainExperience, ...] = ()
    """Industry and domain experience, each citing evidence."""

    credentials: tuple[Credential, ...] = ()
    """Credentials, certifications and qualifications the person holds."""

    preferred_role_types: tuple[NonEmptyStr, ...] = ()
    """Role types the person wants, for example ``technical project manager``."""

    excluded_role_types: tuple[NonEmptyStr, ...] = ()
    """Role types the person will not take."""

    eligibility: tuple[EligibilityConstraint, ...] = ()
    """Work or contracting eligibility, where relevant."""

    commercial_expectations: CommercialExpectations | None = None
    """Minimum commercial expectations, if any apply."""

    @property
    def subject(self) -> SubjectRef:
        """This person as a match target."""
        return SubjectRef.person(self.id)


class CompanyProfile(DomainModel):
    """The delivery organisation an opportunity may be matched against.

    The company is matched independently of its employees: an opportunity may
    be a strong company match even when no single employee covers the whole
    required capability set.

    A delivery organisation is not necessarily one legal entity. Capabilities,
    evidence and project references belong here, held once, because the same
    people do the work whichever entity contracts for it. Legal identity —
    registration, tax numbers, registered office — belongs to the
    :class:`~acquisition.domain.values.ContractingEntity` entries below.
    """

    id: CompanyId
    """Stable identifier of the delivery organisation, not of any one legal entity."""

    name: NonEmptyStr
    """The name the organisation is known by."""

    website: HttpUrl | None = None
    """The organisation's website."""

    contracting_entities: tuple[ContractingEntity, ...] = ()
    """The legal entities work can be ordered from and invoiced by."""

    capabilities: tuple[DemonstratedCapability, ...] = ()
    """Delivery capabilities, each citing evidence."""

    technologies: tuple[DemonstratedCapability, ...] = ()
    """Technologies the company works with, each citing evidence."""

    industries: tuple[DomainExperience, ...] = ()
    """Industries and domains the company has delivered in."""

    supported_commercial_arrangements: tuple[CommercialArrangement, ...] = ()
    """Contracting and pricing arrangements the company supports."""

    geographic_constraints: GeographicScope | None = None
    """Where the company will take work."""

    credentials: tuple[Credential, ...] = ()
    """Credentials and certifications, with status, scope, validity and evidence."""

    supplier_qualifications: tuple[Credential, ...] = ()
    """Qualifications held as an approved supplier, where relevant."""

    project_references: tuple[ProjectReference, ...] = ()
    """Delivered projects the company can point at."""

    employee_ids: tuple[PersonId, ...] = ()
    """Employees who make up the company's delivery capacity.

    An employee may be named before their profile has been written, so these
    identifiers are not required to resolve to a profile.
    """

    stated_capacity: Availability | None = None
    """Capacity as stated directly, where it is not derived from employees."""

    commercial_constraints: CommercialExpectations | None = None
    """Commercial minimums the company works within."""

    languages: tuple[LanguageSkill, ...] = ()
    """Languages the company can deliver in."""

    eligibility: tuple[EligibilityConstraint, ...] = ()
    """Contracting eligibility, where relevant."""

    @model_validator(mode="after")
    def _check_entity_references(self) -> Self:
        known: set[str] = set()
        for entity in self.contracting_entities:
            if entity.id in known:
                raise ValueError(f"duplicate contracting entity id {entity.id!r}")
            known.add(entity.id)

        for credential in (*self.credentials, *self.supplier_qualifications):
            for entity_id in credential.entity_ids:
                if entity_id not in known:
                    raise ValueError(
                        f"credential {credential.id!r} names unknown "
                        f"contracting entity {entity_id!r}"
                    )

        for reference in self.project_references:
            if reference.delivered_by is not None and reference.delivered_by not in known:
                raise ValueError(
                    f"project reference {reference.id!r} names unknown "
                    f"contracting entity {reference.delivered_by!r}"
                )
        return self

    @property
    def subject(self) -> SubjectRef:
        """This company as a match target."""
        return SubjectRef.company(self.id)

    @property
    def entities_by_id(self) -> dict[str, ContractingEntity]:
        """The contracting entities, indexed by identifier."""
        return {entity.id: entity for entity in self.contracting_entities}

    def credentials_for(self, entity_id: str) -> tuple[Credential, ...]:
        """Every credential and supplier qualification covering one entity.

        A credential with no entities named covers all of them.
        """
        return tuple(
            credential
            for credential in (*self.credentials, *self.supplier_qualifications)
            if not credential.entity_ids or entity_id in credential.entity_ids
        )
