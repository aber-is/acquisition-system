"""Match results and rejections."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from acquisition.domain import (
    CapabilityGap,
    EvidenceRef,
    FitAssessment,
    FitLevel,
    MatchHighlight,
    MatchResult,
    Rejection,
    RejectionReason,
    Requirement,
    RequirementImportance,
    SubjectRef,
)


def make_match(**overrides: object) -> MatchResult:
    fields: dict[str, object] = {
        "opportunity_id": "freelancermap-it-project-manager-zurich",
        "target": SubjectRef.person("salomon"),
        "overall_score": 78.0,
        "summary": "Strong infrastructure fit at 20-30%, German level unconfirmed.",
    }
    fields.update(overrides)
    return MatchResult(**fields)  # type: ignore[arg-type]


def test_every_component_defaults_to_unknown() -> None:
    match = make_match()

    assert match.workload_fit.level is FitLevel.unknown
    assert match.availability_fit.level is FitLevel.unknown
    assert match.domain_fit.level is FitLevel.unknown
    assert match.qualification_fit.level is FitLevel.unknown
    assert match.commercial_fit.level is FitLevel.unknown
    assert match.geographic_fit.level is FitLevel.unknown


def test_an_assessed_component_must_explain_itself() -> None:
    with pytest.raises(ValidationError, match="must state its rationale"):
        FitAssessment(level=FitLevel.strong)


def test_an_unknown_component_may_list_what_could_not_be_determined() -> None:
    assessment = FitAssessment(unknowns=("required German level is not stated",))

    assert assessment.level is FitLevel.unknown
    assert assessment.rationale is None


def test_a_strong_match_must_reference_evidence() -> None:
    with pytest.raises(ValidationError):
        MatchHighlight(description="Deep NixOS experience", evidence=())


def test_a_scored_match_carries_highlights_gaps_and_provenance() -> None:
    match = make_match(
        strong_matches=(
            MatchHighlight(
                subject="infrastructure",
                description="Ran production NixOS infrastructure end to end.",
                evidence=(EvidenceRef(evidence_id="cloud-server-config"),),
            ),
        ),
        capability_gaps=(
            CapabilityGap(
                subject="sap",
                description="No demonstrated SAP experience.",
                importance=RequirementImportance.preferred,
            ),
        ),
        workload_fit=FitAssessment(
            level=FitLevel.strong,
            rationale="20-30% requested against up to 30% available.",
        ),
        scored_at=datetime(2026, 9, 25, 8, 0),
    )

    assert match.strong_matches[0].evidence[0].evidence_id == "cloud-server-config"
    assert match.capability_gaps[0].importance is RequirementImportance.preferred
    assert match.overall_score == 78.0


def test_scores_stay_on_the_documented_scale() -> None:
    with pytest.raises(ValidationError):
        make_match(overall_score=120)


def test_relevant_people_belong_to_a_company_match() -> None:
    match = make_match(
        target=SubjectRef.company("aber-industrial-solutions"),
        relevant_people=("salomon", "mark"),
    )

    assert match.relevant_people == ("salomon", "mark")


def test_relevant_people_are_rejected_for_a_person_match() -> None:
    with pytest.raises(ValidationError, match="only be listed for a company match"):
        make_match(relevant_people=("mark",))


class TestRejection:
    def test_a_rejection_carries_a_reason_code(self) -> None:
        rejection = Rejection(
            opportunity_id="freelancermap-permanent-role",
            reason=RejectionReason.employment_only,
            source_text="Festanstellung, keine Freelancer",
        )

        assert rejection.reason is RejectionReason.employment_only
        assert rejection.target is None

    def test_an_other_rejection_must_explain_itself(self) -> None:
        with pytest.raises(ValidationError, match="must state a detail"):
            Rejection(opportunity_id="x", reason=RejectionReason.other)

    def test_a_cited_requirement_must_be_explicit_and_mandatory(self) -> None:
        with pytest.raises(ValidationError, match="only an explicit mandatory requirement"):
            Rejection(
                opportunity_id="x",
                reason=RejectionReason.missing_required_qualification,
                requirement=Requirement(
                    description="ISO 27001 lead auditor",
                    importance=RequirementImportance.preferred,
                    source_text="ISO 27001 Lead Auditor von Vorteil",
                ),
            )

    def test_a_rejection_may_cite_the_mandatory_requirement_that_caused_it(self) -> None:
        rejection = Rejection(
            opportunity_id="x",
            reason=RejectionReason.missing_required_qualification,
            target=SubjectRef.company("aber-industrial-solutions"),
            requirement=Requirement(
                description="ISO 9001 certification",
                importance=RequirementImportance.mandatory,
                source_text="ISO 9001 Zertifizierung zwingend",
            ),
            detail="Certification is in progress, not yet issued.",
        )

        assert rejection.requirement is not None
        assert rejection.requirement.may_cause_rejection
