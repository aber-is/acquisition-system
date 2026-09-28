"""JSON and YAML round-tripping."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from acquisition.domain import (
    AnyOpportunity,
    CommercialArrangement,
    IndividualOpportunity,
    MatchResult,
    OpportunityType,
    PersonProfile,
    ProfileCatalogue,
    SubjectRef,
    from_json,
    from_yaml,
    read_yaml_file,
    to_json,
    to_yaml,
    write_yaml_file,
)


def test_an_opportunity_round_trips_through_json(
    project_manager_opportunity: IndividualOpportunity,
) -> None:
    restored = from_json(IndividualOpportunity, to_json(project_manager_opportunity))

    assert restored == project_manager_opportunity


def test_an_opportunity_round_trips_through_yaml(
    project_manager_opportunity: IndividualOpportunity,
) -> None:
    restored = from_yaml(IndividualOpportunity, to_yaml(project_manager_opportunity))

    assert restored == project_manager_opportunity


def test_the_union_recovers_the_right_type_from_yaml(
    project_manager_opportunity: IndividualOpportunity,
) -> None:
    restored = from_yaml(AnyOpportunity, to_yaml(project_manager_opportunity))

    assert isinstance(restored, IndividualOpportunity)
    assert restored == project_manager_opportunity


def test_a_person_profile_round_trips_through_yaml(salomon: PersonProfile) -> None:
    restored = from_yaml(PersonProfile, to_yaml(salomon))

    assert restored == salomon


def test_yaml_keeps_the_readable_shapes_from_the_domain_model_document(
    salomon: PersonProfile,
) -> None:
    document = yaml.safe_load(to_yaml(salomon))

    assert document["capabilities"][0]["evidence"][0] == {
        "evidence_id": "cloud-server-config",
        "note": "Grafana, Loki and Alloy over mTLS, with custom dashboards.",
    }


def test_a_catalogue_round_trips_through_yaml(catalogue: ProfileCatalogue) -> None:
    assert from_yaml(ProfileCatalogue, to_yaml(catalogue)) == catalogue


def test_a_subject_reference_still_serializes_compactly() -> None:
    match = MatchResult(
        opportunity_id="x",
        target=SubjectRef.company("aber-industrial-solutions"),
        overall_score=50,
        summary="Adequate.",
    )

    assert yaml.safe_load(to_yaml(match))["target"] == "company:aber-industrial-solutions"


def test_yaml_written_by_hand_validates(tmp_path: Path) -> None:
    source = """
    id: simap-framework-industrial-software
    opportunity_type: company_opportunity
    title: Framework agreement for industrial software engineering
    source_id: simap
    source_url: https://www.simap.ch/example
    original_text: Rahmenvertrag für industrielle Softwareentwicklung.
    first_seen_date: 2026-09-01
    last_seen_date: 2026-09-25
    formal_tender: true
    commercial_arrangements:
      state: known
      value: [b2b]
      source_text: Rahmenvertrag
      extraction:
        method: manual
    """
    path = tmp_path / "opportunity.yaml"
    path.write_text(source, encoding="utf-8")

    opportunity = read_yaml_file(AnyOpportunity, path)

    assert opportunity.opportunity_type is OpportunityType.company_opportunity
    assert opportunity.formal_tender
    assert opportunity.commercial_arrangements.value == (CommercialArrangement.b2b,)


def test_writing_and_reading_a_yaml_file(
    tmp_path: Path, project_manager_opportunity: IndividualOpportunity
) -> None:
    path = tmp_path / "opportunity.yaml"
    write_yaml_file(project_manager_opportunity, path)

    assert read_yaml_file(IndividualOpportunity, path) == project_manager_opportunity


def test_invalid_yaml_is_rejected_rather_than_silently_accepted(tmp_path: Path) -> None:
    path = tmp_path / "opportunity.yaml"
    path.write_text("id: x\ntitle: Missing everything else\n", encoding="utf-8")

    with pytest.raises(ValidationError):
        read_yaml_file(IndividualOpportunity, path)
