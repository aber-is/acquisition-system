"""Results of matching an opportunity against a person or the company, and rejections.

``MatchResult.overall_score`` uses a fixed 0-100 scale. The model returns the
structured component assessments, reasons, gaps and evidence references; the
overall score is then calculated deterministically from those components by the
scoring stage rather than accepted as an unexplained model output.
"""

from __future__ import annotations

from datetime import datetime
from typing import Self

from pydantic import Field, model_validator

from .base import DomainModel, NonEmptyStr, OpportunityId, PersonId, Score, Slug
from .enums import FitLevel, RejectionReason, RequirementImportance, SubjectType
from .normalization import ExtractionProvenance
from .opportunity import Requirement
from .values import EvidenceRef, SubjectRef


class FitAssessment(DomainModel):
    """One assessed component of a match.

    The default is ``unknown``: missing information is never treated as
    satisfied. Any other level has to be explained.
    """

    level: FitLevel = FitLevel.unknown
    """How well this component fits."""

    rationale: NonEmptyStr | None = None
    """Why the level was chosen. Required whenever the level is not ``unknown``."""

    evidence: tuple[EvidenceRef, ...] = ()
    """Evidence supporting the assessment."""

    unknowns: tuple[NonEmptyStr, ...] = ()
    """What could not be determined, and therefore did not count as satisfied."""

    @model_validator(mode="after")
    def _check_rationale(self) -> Self:
        if self.level is not FitLevel.unknown and self.rationale is None:
            raise ValueError("an assessed fit must state its rationale")
        return self


class MatchHighlight(DomainModel):
    """A strong match, which must reference the evidence that supports it."""

    description: NonEmptyStr
    """What matches, in words."""

    subject: Slug | None = None
    """The normalized capability or domain this highlight concerns."""

    evidence: tuple[EvidenceRef, ...] = Field(min_length=1)
    """Evidence from the matched profile supporting the claim."""


class CapabilityGap(DomainModel):
    """Something the opportunity asks for that the profile does not demonstrate."""

    description: NonEmptyStr
    """What is missing, in words."""

    subject: Slug | None = None
    """The normalized capability or domain that is missing."""

    importance: RequirementImportance = RequirementImportance.unknown
    """How strongly the opportunity asks for it."""


class MatchResult(DomainModel):
    """The result of matching one opportunity against one person or the company."""

    opportunity_id: OpportunityId
    """The opportunity that was assessed."""

    target: SubjectRef
    """The person or company the opportunity was assessed for."""

    overall_score: Score
    """Score on the fixed 0-100 scale, calculated from the component assessments."""

    summary: NonEmptyStr
    """A concise explanation of the result, suitable for the weekly report."""

    relevant_people: tuple[PersonId, ...] = ()
    """For a company match, the employees who would be involved."""

    strong_matches: tuple[MatchHighlight, ...] = ()
    """Positive claims, each referencing evidence."""

    capability_gaps: tuple[CapabilityGap, ...] = ()
    """What the profile does not cover."""

    evidence: tuple[EvidenceRef, ...] = ()
    """Evidence relevant to the match as a whole."""

    workload_fit: FitAssessment = Field(default_factory=FitAssessment)
    """Whether the requested workload fits the available capacity."""

    availability_fit: FitAssessment = Field(default_factory=FitAssessment)
    """Whether the timing fits."""

    domain_fit: FitAssessment = Field(default_factory=FitAssessment)
    """Whether the industry or domain fits."""

    qualification_fit: FitAssessment = Field(default_factory=FitAssessment)
    """Whether required credentials and qualifications are held."""

    commercial_fit: FitAssessment = Field(default_factory=FitAssessment)
    """Whether the published terms fit the commercial expectations.

    Assessed separately from technical fit, because a technically strong match
    may still be commercially unsuitable.
    """

    geographic_fit: FitAssessment = Field(default_factory=FitAssessment)
    """Whether the location and travel requirements fit."""

    scored_at: datetime | None = None
    """When the match was scored."""

    assessment_provenance: ExtractionProvenance | None = None
    """Which model or rule set produced the component assessments."""

    @model_validator(mode="after")
    def _check_relevant_people(self) -> Self:
        if self.target.subject_type is SubjectType.person and self.relevant_people:
            raise ValueError("relevant people may only be listed for a company match")
        return self


class Rejection(DomainModel):
    """Why an opportunity was excluded.

    Rejected opportunities are normally kept so that rejection patterns can be
    analysed later.
    """

    opportunity_id: OpportunityId
    """The opportunity that was rejected."""

    reason: RejectionReason
    """The machine-readable reason code."""

    target: SubjectRef | None = None
    """The person or company the rejection applies to. Absent when it applies to everyone."""

    detail: NonEmptyStr | None = None
    """Human-readable detail. Required when the reason is ``other``."""

    requirement: Requirement | None = None
    """The requirement that caused the rejection, where one did."""

    source_text: NonEmptyStr | None = None
    """The posting text supporting the rejection."""

    rejected_at: datetime | None = None
    """When the rejection was recorded."""

    @model_validator(mode="after")
    def _check_reason_support(self) -> Self:
        if self.reason is RejectionReason.other and self.detail is None:
            raise ValueError("a rejection with reason 'other' must state a detail")
        if self.requirement is not None and not self.requirement.may_cause_rejection:
            raise ValueError(
                "only an explicit mandatory requirement may cause a deterministic rejection"
            )
        return self
