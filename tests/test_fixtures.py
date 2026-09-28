"""The checked-in catalogue, sources and example opportunities must stay valid.

These fixtures are the domain layer's contact with real data. If a model change breaks
them, that is the signal to look at — not a reason to edit the data.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from acquisition.domain import (
    AnyOpportunity,
    CredentialKind,
    CredentialStatus,
    ProfileCatalogue,
    Source,
    ValueState,
    WorkLocationMode,
    load_profile_catalogue,
    read_yaml_file,
)

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPOSITORY_ROOT / "data"
OPPORTUNITY_DIR = REPOSITORY_ROOT / "examples" / "opportunities"

OPPORTUNITY_FILES = sorted(OPPORTUNITY_DIR.glob("*.yaml"))


@pytest.fixture(scope="module")
def catalogue() -> ProfileCatalogue:
    return load_profile_catalogue(DATA_DIR)


def test_the_sources_file_validates() -> None:
    sources = read_yaml_file(list[Source], DATA_DIR / "sources.yaml")

    assert {source.id for source in sources} == {
        "freelancermap",
        "prostaff",
        "ghr",
        "linkedin",
        "simap",
    }


def test_the_catalogue_loads_and_every_citation_resolves(catalogue: ProfileCatalogue) -> None:
    assert catalogue.company.id == "aber-industrial-solutions"
    assert [person.id for person in catalogue.people] == ["guenter", "mark", "salomon"]
    assert len(catalogue.evidence.items) >= 25


def test_every_person_claim_resolves_to_evidence(catalogue: ProfileCatalogue) -> None:
    for person in catalogue.people:
        claims = (*person.capabilities, *person.domains)
        assert claims, person.id
        for claim in claims:
            assert claim.evidence, f"{person.id}: {claim.subject}"
            for reference in claim.evidence:
                assert catalogue.evidence.resolve(reference)


def test_the_company_profile_is_fully_evidenced(catalogue: ProfileCatalogue) -> None:
    company = catalogue.company

    assert company.employee_ids == ("salomon", "mark", "guenter")
    assert len(company.project_references) >= 5
    assert catalogue.employees_without_profiles() == ()


def test_both_contracting_entities_are_recorded(catalogue: ProfileCatalogue) -> None:
    entities = catalogue.company.entities_by_id

    assert set(entities) == {"mark-aber-freiberuflich", "aber-industrial-solutions-ltd"}
    assert entities["mark-aber-freiberuflich"].country == "DE"
    assert entities["aber-industrial-solutions-ltd"].country == "GB"
    assert entities["mark-aber-freiberuflich"].registration_number is None
    assert entities["aber-industrial-solutions-ltd"].registration_number == "14205293"


def test_each_entity_carries_its_own_supplier_number(catalogue: ProfileCatalogue) -> None:
    """A bid must quote the number of the entity bidding, not the other one's."""
    company = catalogue.company

    def supplier_reference(entity_id: str) -> str | None:
        for credential in company.credentials_for(entity_id):
            if credential.kind is CredentialKind.supplier_qualification:
                return credential.reference
        return None

    assert supplier_reference("mark-aber-freiberuflich") == "LN 10164390"
    assert supplier_reference("aber-industrial-solutions-ltd") == "LN 15152697"


def test_the_iso_certificates_cover_both_entities(catalogue: ProfileCatalogue) -> None:
    company = catalogue.company

    for entity_id in company.entities_by_id:
        certified = {
            credential.id
            for credential in company.credentials_for(entity_id)
            if credential.kind is CredentialKind.certification
            and credential.status is CredentialStatus.active
        }
        assert certified == {"iso-9001-2015", "iso-27001-2022"}, entity_id


def test_the_old_references_belong_to_the_older_entity(catalogue: ProfileCatalogue) -> None:
    """Procurement asks for references delivered by the bidding entity itself."""
    attributed = {
        reference.id: reference.delivered_by
        for reference in catalogue.company.project_references
        if reference.delivered_by is not None
    }

    assert attributed
    assert set(attributed.values()) == {"mark-aber-freiberuflich"}


def test_shared_evidence_is_stored_once(catalogue: ProfileCatalogue) -> None:
    """The point of the library: a project both parties rely on exists in one place."""
    personal = {item.id for item in catalogue.cited_evidence(catalogue.person("salomon"))}
    corporate = {item.id for item in catalogue.cited_evidence(catalogue.company)}
    shared = personal & corporate

    assert len(shared) >= 5
    for evidence_id in shared:
        assert sum(item.id == evidence_id for item in catalogue.evidence.items) == 1


def test_no_capability_is_claimed_by_a_person_without_a_contribution_note(
    catalogue: ProfileCatalogue,
) -> None:
    """A person's citation says what they did; that note is what makes the claim theirs."""
    for person in catalogue.people:
        for claim in person.capabilities:
            assert all(reference.note for reference in claim.evidence), (
                f"{person.id}: {claim.subject}"
            )


def test_two_people_cite_the_same_evidence_for_different_contributions(
    catalogue: ProfileCatalogue,
) -> None:
    """The library holds one item; each profile says what that person did on it."""
    by_person = {
        person.id: {item.id for item in catalogue.cited_evidence(person)}
        for person in catalogue.people
    }
    shared = by_person["mark"] & by_person["salomon"]

    assert shared
    for evidence_id in shared:
        assert sum(item.id == evidence_id for item in catalogue.evidence.items) == 1


def test_the_person_does_not_claim_the_company_only_intouch_work(
    catalogue: ProfileCatalogue,
) -> None:
    """Rastatt-era InTouch work predates Salomon, so it must not appear in his profile."""
    salomon = catalogue.person("salomon")
    claimed = {claim.subject for claim in salomon.capabilities}
    cited = {item.id for item in catalogue.cited_evidence(salomon)}

    assert "wonderware-intouch" not in claimed
    assert "integra-scada-standard-rastatt" not in cited
    assert "wonderware-intouch" in {claim.subject for claim in catalogue.company.capabilities}


def test_every_example_opportunity_validates() -> None:
    assert OPPORTUNITY_FILES, "no example opportunities found"

    for path in OPPORTUNITY_FILES:
        opportunity = read_yaml_file(AnyOpportunity, path)

        assert opportunity.original_text.strip()
        assert opportunity.last_seen_date >= opportunity.first_seen_date


def test_the_opportunity_sources_all_exist() -> None:
    known = {source.id for source in read_yaml_file(list[Source], DATA_DIR / "sources.yaml")}

    for path in OPPORTUNITY_FILES:
        assert read_yaml_file(AnyOpportunity, path).source_id in known


def test_a_quantified_hybrid_arrangement_is_retained() -> None:
    opportunity = read_yaml_file(
        AnyOpportunity, OPPORTUNITY_DIR / "freelancermap-scada-engineer.yaml"
    )

    assert opportunity.work_location.value is not None
    assert opportunity.work_location.value.mode is WorkLocationMode.hybrid
    assert opportunity.work_location.value.onsite_days_per_week == 2
    assert opportunity.work_location.value.remote_share_percentage is None


def test_the_vague_listing_keeps_its_contradictions_unresolved() -> None:
    """A bad listing must survive normalization without inventing hard-filter inputs."""
    opportunity = read_yaml_file(
        AnyOpportunity, OPPORTUNITY_DIR / "prostaff-vague-agency-listing.yaml"
    )

    assert opportunity.workload.state is ValueState.conflicting
    assert opportunity.workload.value is None
    assert len(opportunity.workload.candidates) == 2
    assert not opportunity.status.is_known
    assert not opportunity.commercial_arrangements.is_known
    assert opportunity.mandatory_requirements == ()

    # The mode is stated, the split is not, and no share was invented from "ein Teil".
    assert opportunity.work_location.value is not None
    assert opportunity.work_location.value.mode is WorkLocationMode.hybrid
    assert opportunity.work_location.value.onsite_days_per_week is None
    assert opportunity.work_location.value.remote_share_percentage is None
