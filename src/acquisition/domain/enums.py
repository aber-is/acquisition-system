"""Closed vocabularies used by the domain model.

The values follow the terminology of ``docs/domain-model.md``. New members
should only be added once a real opportunity or profile demonstrates that they
are necessary.
"""

from __future__ import annotations

from enum import StrEnum


class SubjectType(StrEnum):
    """What kind of thing a profile, evidence item or match result refers to."""

    person = "person"
    company = "company"


class ValueState(StrEnum):
    """Whether a normalized value could be determined from the source."""

    known = "known"
    unknown = "unknown"
    conflicting = "conflicting"


class ExtractionMethod(StrEnum):
    """How a normalized value was obtained."""

    source_metadata = "source_metadata"
    rule_based = "rule_based"
    llm = "llm"
    manual = "manual"
    unknown = "unknown"


class OpportunityType(StrEnum):
    """What the client is primarily buying."""

    individual_opportunity = "individual_opportunity"
    company_opportunity = "company_opportunity"


class OpportunityStatus(StrEnum):
    """Listing status of an opportunity.

    ``closed`` means the source explicitly indicates that the opportunity is no
    longer accepting responses. ``expired`` means a known deadline has passed.
    An opportunity disappearing from a source proves neither.
    """

    open = "open"
    closed = "closed"
    expired = "expired"
    unknown = "unknown"


class CommercialArrangement(StrEnum):
    """A contracting or pricing arrangement, independent of :class:`OpportunityType`."""

    direct_freelance = "direct_freelance"
    b2b = "b2b"
    subcontractor = "subcontractor"
    fixed_price = "fixed_price"
    hourly_or_daily_rate = "hourly_or_daily_rate"
    unknown = "unknown"


class RateUnit(StrEnum):
    """The period a published rate refers to."""

    hour = "hour"
    day = "day"
    week = "week"
    month = "month"
    year = "year"
    project = "project"


class RequirementCategory(StrEnum):
    """What kind of thing an opportunity is asking for."""

    capability = "capability"
    language = "language"
    qualification = "qualification"
    experience = "experience"
    eligibility = "eligibility"
    other = "other"


class RequirementImportance(StrEnum):
    """How strongly the source states a requirement.

    Only ``mandatory`` requirements that are explicitly supported by the source
    may cause deterministic rejection.
    """

    mandatory = "mandatory"
    preferred = "preferred"
    optional = "optional"
    unknown = "unknown"


class RejectionReason(StrEnum):
    """Machine-readable reason code for a conclusion drawn against an opportunity.

    A rejection labels an opportunity rather than deleting it. Whether a given
    reason keeps the opportunity out of the weekly report or merely annotates it
    is configured policy, not a property of the code itself.
    """

    workload_too_high = "workload_too_high"
    outside_geography = "outside_geography"
    employment_only = "employment_only"
    missing_required_skill = "missing_required_skill"
    missing_required_qualification = "missing_required_qualification"
    language_requirement = "language_requirement"
    eligibility_requirement = "eligibility_requirement"
    rate_too_low = "rate_too_low"
    unsuitable_role_type = "unsuitable_role_type"
    no_b2b_option = "no_b2b_option"
    unavailable_capacity = "unavailable_capacity"
    deadline_passed = "deadline_passed"
    opportunity_closed = "opportunity_closed"
    other = "other"


class FitLevel(StrEnum):
    """How well one assessed component of a match fits.

    ``unknown`` is the default: missing information is unknown rather than
    assumed satisfied.
    """

    strong = "strong"
    adequate = "adequate"
    partial = "partial"
    poor = "poor"
    unknown = "unknown"


class WorkLocationMode(StrEnum):
    """Where the work is performed."""

    onsite = "onsite"
    hybrid = "hybrid"
    remote = "remote"
    unknown = "unknown"


class LanguageLevel(StrEnum):
    """CEFR language level, plus unassessed bands and ``unknown``.

    Most sources and most people describe language ability without a CEFR
    assessment, so forcing their wording onto the CEFR scale would invent
    precision. ``intermediate`` and ``professional`` are the unassessed bands:
    some working ability, and enough to work and deliver in. ``professional`` is
    also the honest level for an organisation, which has no CEFR level, and for
    the phrasing sources actually use — ``verhandlungssicher``,
    ``business fluent``.
    """

    a1 = "a1"
    a2 = "a2"
    b1 = "b1"
    b2 = "b2"
    c1 = "c1"
    c2 = "c2"
    intermediate = "intermediate"
    professional = "professional"
    native = "native"
    unknown = "unknown"


class LegalForm(StrEnum):
    """The legal form of a contracting entity."""

    limited_company = "limited_company"
    sole_trader = "sole_trader"
    partnership = "partnership"
    other = "other"


class CredentialKind(StrEnum):
    """What kind of credential, certification or qualification is held."""

    certification = "certification"
    qualification = "qualification"
    accreditation = "accreditation"
    membership = "membership"
    security_clearance = "security_clearance"
    supplier_qualification = "supplier_qualification"
    other = "other"


class CredentialStatus(StrEnum):
    """Current status of a credential."""

    active = "active"
    in_progress = "in_progress"
    planned = "planned"
    expired = "expired"
    withdrawn = "withdrawn"
    unknown = "unknown"


class EligibilityKind(StrEnum):
    """What kind of work or contracting eligibility a constraint concerns."""

    work_permit = "work_permit"
    residency = "residency"
    citizenship = "citizenship"
    security_clearance = "security_clearance"
    contracting_form = "contracting_form"
    insurance = "insurance"
    registration = "registration"
    other = "other"


class SourceKind(StrEnum):
    """What kind of place an opportunity was discovered in."""

    job_board = "job_board"
    agency = "agency"
    tender_platform = "tender_platform"
    professional_network = "professional_network"
    direct = "direct"
    other = "other"
