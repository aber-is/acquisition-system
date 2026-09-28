"""The matching candidates and the evidence they cite, loaded as one unit.

A profile on its own cannot tell whether its evidence citations point at
anything, because the evidence lives in a shared library. The catalogue is the
level at which that check is possible, so profiles are always loaded through it.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Self

from pydantic import Field, model_validator

from .base import DomainModel, PersonId
from .evidence import Evidence, EvidenceLibrary, iter_evidence_refs
from .profiles import CompanyProfile, PersonProfile
from .serialization import read_yaml_file

COMPANY_FILE = "company.yaml"
"""Name of the company profile file inside a catalogue directory."""

PEOPLE_DIR = "people"
"""Name of the directory holding one YAML file per person profile."""

EVIDENCE_DIR = "evidence"
"""Name of the directory holding YAML files, each a list of evidence items."""


class ProfileCatalogue(DomainModel):
    """The company, its people, and the evidence library all three cite."""

    company: CompanyProfile
    """The delivery organisation, matchable independently of its employees."""

    people: tuple[PersonProfile, ...] = ()
    """The people who may be matched individually."""

    evidence: EvidenceLibrary = Field(default_factory=EvidenceLibrary)
    """Every evidence item, held once and shared by all profiles."""

    @model_validator(mode="after")
    def _check_references(self) -> Self:
        seen: set[str] = set()
        for person in self.people:
            if person.id in seen:
                raise ValueError(f"duplicate person id {person.id!r}")
            seen.add(person.id)

        for profile in (self.company, *self.people):
            unresolved = self.evidence.unresolved(profile)
            if unresolved:
                missing = ", ".join(sorted({item.evidence_id for item in unresolved}))
                raise ValueError(
                    f"profile {profile.id!r} cites evidence that is not in the library: {missing}"
                )
        return self

    @property
    def people_by_id(self) -> dict[str, PersonProfile]:
        """The people, indexed by identifier."""
        return {person.id: person for person in self.people}

    def person(self, person_id: PersonId) -> PersonProfile:
        """Return one person's profile, or raise :class:`KeyError`."""
        try:
            return self.people_by_id[person_id]
        except KeyError:
            raise KeyError(f"unknown person {person_id!r}") from None

    def employees_without_profiles(self) -> tuple[str, ...]:
        """Employees the company names that have no profile yet."""
        known = self.people_by_id
        return tuple(
            employee_id
            for employee_id in self.company.employee_ids
            if employee_id not in known
        )

    def cited_evidence(self, profile: CompanyProfile | PersonProfile) -> tuple[Evidence, ...]:
        """The evidence items a profile cites, in library order and without repeats."""
        cited = {reference.evidence_id for reference in iter_evidence_refs(profile)}
        return tuple(item for item in self.evidence.items if item.id in cited)


def load_profile_catalogue(directory: Path | str) -> ProfileCatalogue:
    """Read a catalogue from disk.

    Expects ``company.yaml``, a ``people/`` directory of person profiles, and an
    ``evidence/`` directory whose YAML files each hold a list of evidence items.
    """
    root = Path(directory)
    return ProfileCatalogue(
        company=read_yaml_file(CompanyProfile, root / COMPANY_FILE),
        people=tuple(
            read_yaml_file(PersonProfile, path)
            for path in sorted((root / PEOPLE_DIR).glob("*.yaml"))
        ),
        evidence=EvidenceLibrary(items=tuple(_read_evidence(root / EVIDENCE_DIR))),
    )


def _read_evidence(directory: Path) -> Iterable[Evidence]:
    for path in sorted(directory.glob("*.yaml")):
        yield from read_yaml_file(list[Evidence], path)
