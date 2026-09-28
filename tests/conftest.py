"""Shared fixtures built from the examples in ``docs/domain-model.md``."""

from __future__ import annotations

from datetime import date

import pytest

from acquisition.domain import (
    Availability,
    CommercialArrangement,
    CompanyProfile,
    DemonstratedCapability,
    Evidence,
    EvidenceLibrary,
    EvidenceRef,
    ExtractionMethod,
    GeoLocation,
    IndividualOpportunity,
    NormalizedValue,
    PersonProfile,
    ProfileCatalogue,
    Requirement,
    RequirementCategory,
    RequirementImportance,
    Workload,
)


@pytest.fixture
def cloud_server_evidence() -> Evidence:
    """The worked evidence example from the domain model document."""
    return Evidence(
        id="cloud-server-config",
        capabilities=("nixos", "linux", "infrastructure", "monitoring", "backups", "security"),
        description=(
            "Production NixOS infrastructure including declarative provisioning, "
            "encrypted disks, secrets management, monitoring, backups and CI."
        ),
        source="company work summary",
    )


@pytest.fixture
def salomon() -> PersonProfile:
    return PersonProfile(
        id="salomon",
        name="Salomon Aengenheyster-Aber",
        availability=Availability(
            available_hours_per_week=12,
            earliest_start_date=date(2026, 10, 1),
            as_of=date(2026, 9, 25),
        ),
        maximum_workload=Workload(maximum_percentage=30, original_text="up to 30%"),
        location=GeoLocation(country="CH", city="Zürich"),
        capabilities=(
            DemonstratedCapability(
                subject="monitoring",
                evidence=(
                    EvidenceRef(
                        evidence_id="cloud-server-config",
                        note="Grafana, Loki and Alloy over mTLS, with custom dashboards.",
                    ),
                ),
            ),
        ),
    )


@pytest.fixture
def company() -> CompanyProfile:
    return CompanyProfile(
        id="aber-industrial-solutions",
        name="Aber Industrial Solutions",
        capabilities=(
            DemonstratedCapability(
                subject="infrastructure",
                evidence=(EvidenceRef(evidence_id="cloud-server-config"),),
            ),
        ),
        supported_commercial_arrangements=(
            CommercialArrangement.b2b,
            CommercialArrangement.fixed_price,
        ),
        employee_ids=("salomon", "mark", "guenter"),
    )


@pytest.fixture
def catalogue(
    company: CompanyProfile, salomon: PersonProfile, cloud_server_evidence: Evidence
) -> ProfileCatalogue:
    """A catalogue where one evidence item is cited by both the person and the company."""
    return ProfileCatalogue(
        company=company,
        people=(salomon,),
        evidence=EvidenceLibrary(items=(cloud_server_evidence,)),
    )


@pytest.fixture
def project_manager_opportunity() -> IndividualOpportunity:
    """Example 1 from the domain model document."""
    return IndividualOpportunity(
        id="freelancermap-it-project-manager-zurich",
        title="Freelance IT Project Manager",
        client="Undisclosed",
        source_id="freelancermap",
        source_url="https://www.freelancermap.ch/projekt/example",
        original_text="Freelance IT Project Manager, Zürich, 20-30%, B2B möglich.",
        first_seen_date=date(2026, 9, 20),
        last_seen_date=date(2026, 9, 25),
        application_deadline=date(2026, 10, 15),
        location=NormalizedValue[GeoLocation].known(
            GeoLocation(country="CH", city="Zürich", original_text="Zürich"),
            source_text="Zürich",
            extraction={"method": ExtractionMethod.rule_based},
        ),
        workload=NormalizedValue[Workload].known(
            Workload(minimum_percentage=20, maximum_percentage=30, original_text="20-30%"),
            source_text="20-30%",
            extraction={"method": ExtractionMethod.rule_based},
        ),
        commercial_arrangements=NormalizedValue[tuple[CommercialArrangement, ...]].known(
            (CommercialArrangement.b2b,),
            source_text="B2B möglich",
            extraction={"method": ExtractionMethod.rule_based},
        ),
        requirements=(
            Requirement(
                description="German at working level",
                category=RequirementCategory.language,
                subject="de",
                importance=RequirementImportance.mandatory,
                source_text="Deutsch zwingend erforderlich",
            ),
        ),
    )
