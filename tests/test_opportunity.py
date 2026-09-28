"""Opportunities, their types, and the requirements they state."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from acquisition.domain import (
    CommercialArrangement,
    CompanyOpportunity,
    IndividualOpportunity,
    OpportunityStatus,
    OpportunityType,
    Requirement,
    RequirementCategory,
    RequirementImportance,
    Source,
    SourceKind,
    opportunity_adapter,
)


def make_company_opportunity(**overrides: object) -> CompanyOpportunity:
    fields: dict[str, object] = {
        "id": "simap-framework-industrial-software",
        "title": "Framework agreement for industrial software engineering",
        "source_id": "simap",
        "source_url": "https://www.simap.ch/example",
        "original_text": "Rahmenvertrag für industrielle Softwareentwicklung.",
        "first_seen_date": date(2026, 9, 1),
        "last_seen_date": date(2026, 9, 25),
        "formal_tender": True,
    }
    fields.update(overrides)
    return CompanyOpportunity(**fields)  # type: ignore[arg-type]


def test_an_individual_opportunity_may_still_be_contracted_business_to_business(
    project_manager_opportunity: IndividualOpportunity,
) -> None:
    assert project_manager_opportunity.opportunity_type is OpportunityType.individual_opportunity
    assert project_manager_opportunity.commercial_arrangements.value == (
        CommercialArrangement.b2b,
    )


def test_a_tender_keeps_its_opportunity_type() -> None:
    tender = make_company_opportunity()

    assert tender.formal_tender
    assert tender.opportunity_type is OpportunityType.company_opportunity


def test_the_original_posting_text_is_required(
    project_manager_opportunity: IndividualOpportunity,
) -> None:
    assert project_manager_opportunity.original_text.startswith("Freelance IT Project Manager")

    with pytest.raises(ValidationError):
        make_company_opportunity(original_text="   ")


def test_a_source_url_must_be_a_url() -> None:
    with pytest.raises(ValidationError):
        make_company_opportunity(source_url="not-a-url")


def test_status_and_location_default_to_unknown() -> None:
    opportunity = make_company_opportunity()

    assert not opportunity.status.is_known
    assert not opportunity.location.is_known
    assert not opportunity.workload.is_known


def test_status_records_what_the_source_said() -> None:
    opportunity = make_company_opportunity(
        status={
            "state": "known",
            "value": OpportunityStatus.closed,
            "source_text": "Diese Ausschreibung ist abgeschlossen.",
        }
    )

    assert opportunity.status.value is OpportunityStatus.closed
    assert opportunity.status.source_text is not None


def test_an_opportunity_cannot_be_last_seen_before_it_was_first_seen() -> None:
    with pytest.raises(ValidationError, match="last seen before"):
        make_company_opportunity(
            first_seen_date=date(2026, 9, 25), last_seen_date=date(2026, 9, 1)
        )


class TestRequirement:
    def test_an_explicit_mandatory_requirement_may_cause_rejection(
        self, project_manager_opportunity: IndividualOpportunity
    ) -> None:
        requirement = project_manager_opportunity.requirements[0]

        assert requirement.category is RequirementCategory.language
        assert requirement.may_cause_rejection
        assert project_manager_opportunity.mandatory_requirements == (requirement,)

    def test_a_mandatory_requirement_without_source_support_may_not(self) -> None:
        requirement = Requirement(
            description="German at working level",
            importance=RequirementImportance.mandatory,
        )

        assert not requirement.is_explicit
        assert not requirement.may_cause_rejection

    @pytest.mark.parametrize(
        "importance",
        [
            RequirementImportance.preferred,
            RequirementImportance.optional,
            RequirementImportance.unknown,
        ],
    )
    def test_non_mandatory_requirements_may_not_cause_rejection(
        self, importance: RequirementImportance
    ) -> None:
        requirement = Requirement(
            description="Experience with SCADA systems",
            importance=importance,
            source_text="SCADA von Vorteil",
        )

        assert not requirement.may_cause_rejection

    def test_importance_defaults_to_unknown(self) -> None:
        assert Requirement(description="Nice handwriting").importance is (
            RequirementImportance.unknown
        )


class TestDiscriminatedUnion:
    def test_the_type_selects_the_model(
        self, project_manager_opportunity: IndividualOpportunity
    ) -> None:
        data = project_manager_opportunity.model_dump(mode="json")

        assert isinstance(opportunity_adapter.validate_python(data), IndividualOpportunity)

    def test_a_company_opportunity_is_recovered_as_a_company_opportunity(self) -> None:
        data = make_company_opportunity().model_dump(mode="json")

        assert isinstance(opportunity_adapter.validate_python(data), CompanyOpportunity)

    def test_the_type_cannot_be_changed_on_a_concrete_model(self) -> None:
        with pytest.raises(ValidationError):
            make_company_opportunity(
                opportunity_type=OpportunityType.individual_opportunity,
            )


def test_a_source_is_described_independently_of_its_opportunities() -> None:
    source = Source(
        id="simap",
        name="SIMAP",
        kind=SourceKind.tender_platform,
        url="https://www.simap.ch/",
    )

    assert source.id == make_company_opportunity().source_id
    assert source.kind is SourceKind.tender_platform
