"""Profiles, and the catalogue that resolves the evidence they cite."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from acquisition.domain import (
    CompanyProfile,
    ContractingEntity,
    Credential,
    CredentialKind,
    CredentialStatus,
    DemonstratedCapability,
    Evidence,
    EvidenceLibrary,
    EvidenceRef,
    GeographicScope,
    LegalForm,
    PersonProfile,
    ProfileCatalogue,
    ProjectReference,
    SubjectRef,
)


def test_a_capability_cannot_be_claimed_without_evidence() -> None:
    with pytest.raises(ValidationError):
        DemonstratedCapability(subject="kubernetes", evidence=())


def test_unknown_profile_fields_are_rejected() -> None:
    with pytest.raises(ValidationError, match="Extra inputs"):
        PersonProfile(id="salomon", name="Salomon", skills=("nixos",))


def test_a_profile_exposes_itself_as_a_match_target(
    salomon: PersonProfile, company: CompanyProfile
) -> None:
    assert salomon.subject == SubjectRef.person("salomon")
    assert company.subject == SubjectRef.company("aber-industrial-solutions")


def test_the_company_is_matchable_without_any_employee_profile() -> None:
    company = CompanyProfile(
        id="aber-industrial-solutions",
        name="Aber Industrial Solutions Ltd",
        geographic_constraints=GeographicScope(countries=("CH",)),
    )

    assert company.employee_ids == ()
    assert company.capabilities == ()


class TestContractingEntities:
    def make_company(self, **overrides: object) -> CompanyProfile:
        fields: dict[str, object] = {
            "id": "aber-industrial-solutions",
            "name": "Aber Industrial Solutions",
            "contracting_entities": (
                ContractingEntity(
                    id="mark-aber-freiberuflich",
                    legal_name="Mark Aber",
                    trading_name="Aber Industrial Solutions",
                    legal_form=LegalForm.sole_trader,
                    country="DE",
                    tax_number="DE178994004",
                ),
                ContractingEntity(
                    id="aber-industrial-solutions-ltd",
                    legal_name="Aber Industrial Solutions Ltd",
                    legal_form=LegalForm.limited_company,
                    country="GB",
                    registration_number="14205293",
                ),
            ),
        }
        fields.update(overrides)
        return CompanyProfile(**fields)  # type: ignore[arg-type]

    def test_a_sole_trader_needs_no_registration_number(self) -> None:
        entity = self.make_company().entities_by_id["mark-aber-freiberuflich"]

        assert entity.legal_form is LegalForm.sole_trader
        assert entity.registration_number is None
        assert entity.tax_number == "DE178994004"

    def test_a_credential_naming_no_entity_covers_every_entity(self) -> None:
        company = self.make_company(
            credentials=(
                Credential(
                    id="iso-9001",
                    kind=CredentialKind.certification,
                    name="ISO 9001:2015",
                    status=CredentialStatus.active,
                ),
            )
        )

        for entity in company.contracting_entities:
            assert [c.id for c in company.credentials_for(entity.id)] == ["iso-9001"]

    def test_a_credential_may_cover_one_entity_only(self) -> None:
        company = self.make_company(
            supplier_qualifications=(
                Credential(
                    id="mercedes-benz-supplier-de",
                    kind=CredentialKind.supplier_qualification,
                    name="Mercedes-Benz AG supplier",
                    reference="LN 10164390",
                    entity_ids=("mark-aber-freiberuflich",),
                    status=CredentialStatus.active,
                ),
            )
        )

        assert company.credentials_for("mark-aber-freiberuflich")
        assert company.credentials_for("aber-industrial-solutions-ltd") == ()

    def test_a_credential_cannot_name_an_entity_that_does_not_exist(self) -> None:
        with pytest.raises(ValidationError, match="names unknown contracting entity"):
            self.make_company(
                credentials=(
                    Credential(
                        id="iso-9001",
                        kind=CredentialKind.certification,
                        name="ISO 9001:2015",
                        entity_ids=("some-other-company",),
                    ),
                )
            )

    def test_a_project_reference_records_which_entity_delivered_it(self) -> None:
        company = self.make_company(
            project_references=(
                ProjectReference(
                    id="mercedes-benz-rastatt-integra",
                    title="Enterprise SCADA architecture",
                    summary="Modernisation of the HMI and SCADA architecture.",
                    delivered_by="mark-aber-freiberuflich",
                ),
            )
        )

        assert company.project_references[0].delivered_by == "mark-aber-freiberuflich"

    def test_a_project_reference_cannot_name_an_entity_that_does_not_exist(self) -> None:
        with pytest.raises(ValidationError, match="names unknown contracting entity"):
            self.make_company(
                project_references=(
                    ProjectReference(
                        id="somebody-elses-project",
                        title="Not ours",
                        summary="Delivered by a company that is not one of ours.",
                        delivered_by="another-company-entirely",
                    ),
                )
            )

    def test_duplicate_entity_ids_are_rejected(self) -> None:
        entity = ContractingEntity(
            id="aber-industrial-solutions-ltd",
            legal_name="Aber Industrial Solutions Ltd",
            country="GB",
        )

        with pytest.raises(ValidationError, match="duplicate contracting entity id"):
            self.make_company(contracting_entities=(entity, entity))


class TestProfileCatalogue:
    def test_one_evidence_item_serves_a_person_and_the_company(
        self, catalogue: ProfileCatalogue
    ) -> None:
        assert len(catalogue.evidence.items) == 1
        assert catalogue.cited_evidence(catalogue.person("salomon"))[0].id == "cloud-server-config"
        assert catalogue.cited_evidence(catalogue.company)[0].id == "cloud-server-config"

    def test_a_citation_carries_what_the_person_contributed(
        self, catalogue: ProfileCatalogue
    ) -> None:
        reference = catalogue.person("salomon").capabilities[0].evidence[0]

        assert reference.note is not None
        assert catalogue.evidence.resolve(reference).id == "cloud-server-config"

    def test_a_citation_must_resolve_to_a_library_item(
        self, company: CompanyProfile, cloud_server_evidence: Evidence
    ) -> None:
        person = PersonProfile(
            id="salomon",
            name="Salomon Aengenheyster-Aber",
            capabilities=(
                DemonstratedCapability(
                    subject="kubernetes",
                    evidence=(EvidenceRef(evidence_id="imagined-project"),),
                ),
            ),
        )

        with pytest.raises(ValidationError, match="not in the library: imagined-project"):
            ProfileCatalogue(
                company=company,
                people=(person,),
                evidence=EvidenceLibrary(items=(cloud_server_evidence,)),
            )

    def test_the_company_citations_are_checked_too(self, company: CompanyProfile) -> None:
        with pytest.raises(ValidationError, match="not in the library: cloud-server-config"):
            ProfileCatalogue(company=company)

    def test_duplicate_evidence_ids_are_rejected(self, cloud_server_evidence: Evidence) -> None:
        with pytest.raises(ValidationError, match="duplicate evidence id"):
            EvidenceLibrary(items=(cloud_server_evidence, cloud_server_evidence))

    def test_duplicate_person_ids_are_rejected(
        self, company: CompanyProfile, salomon: PersonProfile, cloud_server_evidence: Evidence
    ) -> None:
        with pytest.raises(ValidationError, match="duplicate person id"):
            ProfileCatalogue(
                company=company,
                people=(salomon, salomon),
                evidence=EvidenceLibrary(items=(cloud_server_evidence,)),
            )

    def test_an_employee_may_be_named_before_their_profile_exists(
        self, catalogue: ProfileCatalogue
    ) -> None:
        assert catalogue.employees_without_profiles() == ("mark", "guenter")

    def test_resolving_an_unknown_reference_raises(self, catalogue: ProfileCatalogue) -> None:
        with pytest.raises(KeyError, match="unknown evidence"):
            catalogue.evidence.resolve(EvidenceRef(evidence_id="nothing-here"))

    def test_asking_for_an_unknown_person_raises(self, catalogue: ProfileCatalogue) -> None:
        with pytest.raises(KeyError, match="unknown person"):
            catalogue.person("mark")


def test_evidence_must_retain_its_provenance() -> None:
    with pytest.raises(ValidationError, match="source, a URL or its extraction provenance"):
        Evidence(id="unsourced", description="Something happened.")
