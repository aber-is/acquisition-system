"""Small value objects shared by profiles, opportunities and match results."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Self

from pydantic import Field, model_serializer, model_validator

from .base import (
    CountryCode,
    CredentialId,
    CurrencyCode,
    DomainModel,
    EvidenceId,
    HoursPerWeek,
    LanguageCode,
    NonEmptyStr,
    Percentage,
    ProjectId,
    Slug,
)
from .enums import (
    CredentialKind,
    CredentialStatus,
    EligibilityKind,
    LanguageLevel,
    LegalForm,
    RateUnit,
    SubjectType,
    WorkLocationMode,
)
from .normalization import NormalizedValue


class SubjectRef(DomainModel):
    """A reference to the person or company a statement is about.

    Serializes to the compact ``person:salomon`` form used in the domain model
    document, and accepts that form on input.
    """

    subject_type: SubjectType
    """Whether the subject is a person or the company."""

    subject_id: Slug
    """Identifier of the person or company."""

    @model_validator(mode="before")
    @classmethod
    def _parse_compact_form(cls, data: Any) -> Any:
        if isinstance(data, str):
            prefix, separator, identifier = data.partition(":")
            if not separator:
                raise ValueError(
                    "a subject reference must look like 'person:<id>' or 'company:<id>'"
                )
            return {"subject_type": prefix, "subject_id": identifier}
        return data

    @model_serializer
    def _serialize_compact_form(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"{self.subject_type.value}:{self.subject_id}"

    @classmethod
    def person(cls, person_id: str) -> Self:
        """Reference a person by identifier."""
        return cls(subject_type=SubjectType.person, subject_id=person_id)

    @classmethod
    def company(cls, company_id: str) -> Self:
        """Reference the company by identifier."""
        return cls(subject_type=SubjectType.company, subject_id=company_id)


class EvidenceRef(DomainModel):
    """A pointer from a claim to the evidence that supports it.

    Accepts a bare evidence identifier on input so that profiles stay readable
    in YAML.
    """

    evidence_id: EvidenceId
    """Identifier of the referenced evidence item."""

    note: NonEmptyStr | None = None
    """Why this evidence supports the claim it is attached to."""

    @model_validator(mode="before")
    @classmethod
    def _parse_bare_identifier(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"evidence_id": data}
        return data


class DatePeriod(DomainModel):
    """A date or period, used where only partial dating is known."""

    start: date | None = None
    """First day of the period, if known."""

    end: date | None = None
    """Last day of the period, if known. Absent for ongoing work."""

    description: NonEmptyStr | None = None
    """Textual dating for periods that cannot be expressed as dates."""

    @model_validator(mode="after")
    def _check_period(self) -> Self:
        if self.start is not None and self.end is not None and self.end < self.start:
            raise ValueError("a period cannot end before it starts")
        if self.start is None and self.end is None and self.description is None:
            raise ValueError("a period must retain at least one of start, end or description")
        return self


class GeoLocation(DomainModel):
    """Where work is located.

    The initial discovery geography is Switzerland, but that is configuration:
    locations are recorded as stated by the source.
    """

    country: CountryCode | None = None
    """ISO 3166-1 alpha-2 country code."""

    region: NonEmptyStr | None = None
    """Canton, state or comparable subdivision."""

    city: NonEmptyStr | None = None
    """City or municipality."""

    postal_code: NonEmptyStr | None = None
    """Postal code, where the source gives one."""

    original_text: NonEmptyStr | None = None
    """The location exactly as the source stated it."""

    @model_validator(mode="after")
    def _check_not_empty(self) -> Self:
        if not any(
            value is not None
            for value in (self.country, self.region, self.city, self.postal_code,
                          self.original_text)
        ):
            raise ValueError("a location must retain at least one field")
        return self


class GeographicScope(DomainModel):
    """The geography a delivery organisation is willing or able to serve."""

    countries: tuple[CountryCode, ...] = ()
    """Countries that are served. Empty means no country restriction is recorded."""

    regions: tuple[NonEmptyStr, ...] = ()
    """Regions that are served, where narrower than a country."""

    accepted_work_location_modes: tuple[WorkLocationMode, ...] = ()
    """Onsite, hybrid or remote delivery modes that are acceptable."""

    notes: NonEmptyStr | None = None
    """Constraints that do not fit the structured fields."""


class WorkLocationPreference(DomainModel):
    """A person's remote and on-site preferences."""

    accepted_modes: tuple[WorkLocationMode, ...] = Field(min_length=1)
    """Modes the person will accept."""

    preferred_mode: WorkLocationMode | None = None
    """The preferred mode, which must be one of the accepted modes."""

    maximum_commute_km: float | None = Field(default=None, ge=0)
    """Longest one-way commute the person will accept for on-site work."""

    notes: NonEmptyStr | None = None
    """Anything the structured fields do not capture."""

    @model_validator(mode="after")
    def _check_preferred_mode(self) -> Self:
        if self.preferred_mode is not None and self.preferred_mode not in self.accepted_modes:
            raise ValueError("the preferred work location mode must also be an accepted mode")
        return self


class WorkLocationRequirement(DomainModel):
    """Where an opportunity expects the work to be performed.

    Retained separately from the location because the two decide viability
    together: a fully remote engagement in another country may be workable where
    the same engagement on site five days a week is not.

    On-site days and remote share are not converted into one another, for the
    same reason :class:`Workload` does not convert percentages into hours — the
    length of the working week is not necessarily known.
    """

    mode: WorkLocationMode
    """On-site, hybrid or remote. If the source does not say, the value is unknown."""

    onsite_days_per_week: float | None = Field(default=None, ge=0, le=7)
    """Days per week expected on site, where the source quantifies it."""

    remote_share_percentage: Percentage | None = None
    """Share of the work that may be done remotely, where the source quantifies it."""

    original_text: NonEmptyStr | None = None
    """The arrangement exactly as the source stated it."""

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        if self.mode is WorkLocationMode.remote and self.onsite_days_per_week:
            raise ValueError("remote work cannot require on-site days")
        if self.mode is WorkLocationMode.onsite and self.remote_share_percentage:
            raise ValueError("on-site work cannot have a remote share")
        return self


class LanguageSkill(DomainModel):
    """A language a person or company works in."""

    language: LanguageCode
    """ISO 639 language code."""

    level: LanguageLevel = LanguageLevel.unknown
    """CEFR level, ``native``, or ``unknown`` when not stated."""

    evidence: tuple[EvidenceRef, ...] = ()
    """Evidence supporting the stated level."""

    notes: NonEmptyStr | None = None
    """Qualifications on the level, such as a language held natively but out of practice."""


class Workload(DomainModel):
    """How much capacity an opportunity asks for, or a person offers.

    Percentages and hours are kept separately. They are only interchangeable
    when ``full_time_hours_per_week`` records the basis used for the
    conversion, so the conversion helpers return ``None`` without it.
    Open-ended or qualitative values such as ``at least 60%``, ``full-time`` or
    ``negotiable`` may retain only ``original_text``.
    """

    minimum_percentage: Percentage | None = None
    """Lowest share of full time that is acceptable."""

    maximum_percentage: Percentage | None = None
    """Highest share of full time that is acceptable."""

    minimum_hours_per_week: HoursPerWeek | None = None
    """Lowest weekly hours that are acceptable."""

    maximum_hours_per_week: HoursPerWeek | None = None
    """Highest weekly hours that are acceptable."""

    full_time_hours_per_week: HoursPerWeek | None = None
    """The full-time week used to convert between percentages and hours."""

    original_text: NonEmptyStr | None = None
    """The workload exactly as the source stated it."""

    @model_validator(mode="after")
    def _check_ranges(self) -> Self:
        if (
            self.minimum_percentage is not None
            and self.maximum_percentage is not None
            and self.maximum_percentage < self.minimum_percentage
        ):
            raise ValueError("the maximum percentage cannot be below the minimum percentage")
        if (
            self.minimum_hours_per_week is not None
            and self.maximum_hours_per_week is not None
            and self.maximum_hours_per_week < self.minimum_hours_per_week
        ):
            raise ValueError("the maximum hours cannot be below the minimum hours")
        if not any(
            value is not None
            for value in (
                self.minimum_percentage,
                self.maximum_percentage,
                self.minimum_hours_per_week,
                self.maximum_hours_per_week,
                self.original_text,
            )
        ):
            raise ValueError("a workload must retain at least the original text")
        return self

    @property
    def is_convertible(self) -> bool:
        """Whether percentages and hours may be converted into one another."""
        return self.full_time_hours_per_week is not None

    def hours_range(self) -> tuple[float | None, float | None] | None:
        """The workload in weekly hours, or ``None`` when it cannot be derived safely.

        Stated hours are used as they are. Percentages are converted only when
        the full-time week is known.
        """
        minimum, maximum = self.minimum_hours_per_week, self.maximum_hours_per_week
        basis = self.full_time_hours_per_week
        if basis is not None:
            if minimum is None and self.minimum_percentage is not None:
                minimum = basis * self.minimum_percentage / 100
            if maximum is None and self.maximum_percentage is not None:
                maximum = basis * self.maximum_percentage / 100
        if minimum is None and maximum is None:
            return None
        return minimum, maximum

    def percentage_range(self) -> tuple[float | None, float | None] | None:
        """The workload as a share of full time, or ``None`` when it cannot be derived safely."""
        minimum, maximum = self.minimum_percentage, self.maximum_percentage
        basis = self.full_time_hours_per_week
        if basis:
            if minimum is None and self.minimum_hours_per_week is not None:
                minimum = self.minimum_hours_per_week / basis * 100
            if maximum is None and self.maximum_hours_per_week is not None:
                maximum = self.maximum_hours_per_week / basis * 100
        if minimum is None and maximum is None:
            return None
        return minimum, maximum


class AvailabilityChange(DomainModel):
    """A known future change to a person's availability."""

    effective_date: date
    """When the change takes effect."""

    available_hours_per_week: HoursPerWeek | None = None
    """Weekly hours available from that date, if known."""

    description: NonEmptyStr
    """What changes, for example the end of a current engagement."""


class Availability(DomainModel):
    """Current availability, with known future changes.

    Deliberately simple: a full scheduling model is not required.
    """

    available_hours_per_week: HoursPerWeek | None = None
    """Weekly hours currently available."""

    earliest_start_date: date | None = None
    """Earliest date new work could start."""

    known_changes: tuple[AvailabilityChange, ...] = ()
    """Changes that are already known about."""

    as_of: date | None = None
    """When this availability was last confirmed."""

    notes: NonEmptyStr | None = None
    """Anything the structured fields do not capture."""


class Money(DomainModel):
    """An amount in a single currency."""

    amount: Decimal = Field(ge=0)
    """The amount, kept as a decimal to avoid binary rounding."""

    currency: CurrencyCode
    """ISO 4217 currency code."""


class RateRange(DomainModel):
    """A published or expected rate, which may be open at either end."""

    unit: RateUnit
    """The period the rate refers to."""

    minimum: Money | None = None
    """Lowest rate, if stated."""

    maximum: Money | None = None
    """Highest rate, if stated."""

    original_text: NonEmptyStr | None = None
    """The rate exactly as the source stated it."""

    @model_validator(mode="after")
    def _check_range(self) -> Self:
        if self.minimum is not None and self.maximum is not None:
            if self.minimum.currency != self.maximum.currency:
                raise ValueError("a rate range must use one currency")
            if self.maximum.amount < self.minimum.amount:
                raise ValueError("the maximum rate cannot be below the minimum rate")
        if self.minimum is None and self.maximum is None and self.original_text is None:
            raise ValueError("a rate must retain at least the original text")
        return self


class CommercialTerms(DomainModel):
    """The commercial terms an opportunity publishes."""

    rate: RateRange | None = None
    """Published rate, if any."""

    budget: Money | None = None
    """Published budget, if any."""

    estimated_contract_value: Money | None = None
    """Estimated total contract value, if any."""

    payment_terms: NonEmptyStr | None = None
    """Payment terms exactly as stated, for example ``60 days net``."""

    b2b_allowed: NormalizedValue[bool] = Field(
        default_factory=NormalizedValue[bool].unknown
    )
    """Whether contracting through a company is allowed. Used by hard filters."""

    original_text: NonEmptyStr | None = None
    """The commercial section of the posting, as published."""


class CommercialExpectations(DomainModel):
    """The commercial minimums or constraints of a person or the company.

    Which contracting arrangements are supported is recorded on the company
    profile rather than here, so that there is one home for that fact.
    """

    minimum_rate: RateRange | None = None
    """Lowest rate that is acceptable."""

    minimum_engagement_value: Money | None = None
    """Smallest engagement that is worth taking on."""

    notes: NonEmptyStr | None = None
    """Anything the structured fields do not capture."""


class Credential(DomainModel):
    """A credential, certification, qualification or supplier qualification."""

    id: CredentialId
    """Stable identifier within the profile that holds the credential."""

    kind: CredentialKind
    """What kind of credential this is."""

    name: NonEmptyStr
    """Name of the credential as the issuer states it."""

    issuer: NonEmptyStr | None = None
    """Who issued or maintains the credential."""

    status: CredentialStatus = CredentialStatus.unknown
    """Current status of the credential."""

    scope: NonEmptyStr | None = None
    """What the credential covers, for example the certified scope statement."""

    reference: NonEmptyStr | None = None
    """Certificate or registration number."""

    valid_from: date | None = None
    """Start of validity, if known."""

    valid_until: date | None = None
    """End of validity, if known."""

    entity_ids: tuple[Slug, ...] = ()
    """The contracting entities this credential covers. Empty means all of them."""

    notes: NonEmptyStr | None = None
    """Qualifications on the credential, such as doubt about whether it is still current."""

    expected_completion: DatePeriod | None = None
    """When a credential still in progress is expected to be issued or completed.

    A :class:`DatePeriod` rather than a date, because the real answer is often a
    month or a quarter — ``description: "02/2027"`` states that without
    pretending to know the day.
    """

    evidence: tuple[EvidenceRef, ...] = ()
    """Evidence supporting the credential."""

    @model_validator(mode="after")
    def _check_validity(self) -> Self:
        if (
            self.valid_from is not None
            and self.valid_until is not None
            and self.valid_until < self.valid_from
        ):
            raise ValueError("a credential cannot expire before it becomes valid")
        if self.expected_completion is not None and self.status in (
            CredentialStatus.active,
            CredentialStatus.expired,
            CredentialStatus.withdrawn,
        ):
            raise ValueError(
                f"a credential that is {self.status.value} cannot have an expected completion"
            )
        return self


class EligibilityConstraint(DomainModel):
    """A work or contracting eligibility fact about a person or the company.

    ``holds`` records whether the subject has the entitlement. Setting it to
    ``False`` documents a known gap, such as the absence of a work permit for a
    given country.
    """

    kind: EligibilityKind
    """What kind of eligibility this concerns."""

    description: NonEmptyStr
    """The entitlement or restriction in words."""

    holds: bool = True
    """Whether the subject holds the entitlement."""

    country: CountryCode | None = None
    """Country the eligibility applies to, where it is country-specific."""

    valid_until: date | None = None
    """When the entitlement lapses, if it is time-limited."""

    evidence: tuple[EvidenceRef, ...] = ()
    """Evidence supporting the eligibility."""


class TravelRequirement(DomainModel):
    """Travel an opportunity requires."""

    description: NonEmptyStr
    """The travel requirement as stated by the source."""

    share_percentage: Percentage | None = None
    """Share of working time spent travelling, if quantified."""

    destinations: tuple[GeoLocation, ...] = ()
    """Where the travel goes, if stated."""


class ContractingEntity(DomainModel):
    """A legal entity that work can be ordered from and invoiced by.

    A delivery organisation may contract through more than one entity, in more
    than one jurisdiction. Which one is used is often a fiscal decision, but it
    is not only that: an entity's jurisdiction and trading history can decide
    whether a buyer may award to it at all.

    Capabilities and evidence belong to the delivery organisation, not here.
    This records only who signs, invoices, and is registered where.
    """

    id: Slug
    """Stable identifier, cited by credentials and project references."""

    legal_name: NonEmptyStr
    """The entity's registered or legal name."""

    trading_name: NonEmptyStr | None = None
    """The name it trades under, where that differs from the legal name."""

    legal_form: LegalForm = LegalForm.other
    """Whether it is a company, a sole trader, or something else."""

    country: CountryCode
    """Country of registration or establishment."""

    registration_number: NonEmptyStr | None = None
    """Commercial register identifier. A sole trader may not have one."""

    tax_number: NonEmptyStr | None = None
    """Tax or VAT identifier, such as a UK VAT number or a German USt-IdNr."""

    location: GeoLocation | None = None
    """Registered office or place of establishment."""

    established: DatePeriod | None = None
    """When the entity began trading, where it is known."""

    notes: NonEmptyStr | None = None
    """Anything the structured fields do not capture."""


class ProjectReference(DomainModel):
    """A delivered project the company can refer to."""

    id: ProjectId
    """Stable identifier of the reference."""

    delivered_by: Slug | None = None
    """The contracting entity that delivered it.

    Procurement commonly asks for references delivered by the bidding entity
    itself, so a reference earned under a predecessor or sibling entity may not
    be citable in every bid.
    """

    title: NonEmptyStr
    """Short name of the project."""

    summary: NonEmptyStr
    """What was delivered."""

    client: NonEmptyStr | None = None
    """The client, where it may be named."""

    period: DatePeriod | None = None
    """When the project ran."""

    capabilities: tuple[Slug, ...] = ()
    """Capabilities the project demonstrates."""

    evidence: tuple[EvidenceRef, ...] = ()
    """Evidence supporting the reference."""
