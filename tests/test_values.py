"""Value objects: workload, availability, money, geography and credentials."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from acquisition.domain import (
    Credential,
    CredentialKind,
    CredentialStatus,
    DatePeriod,
    GeoLocation,
    LanguageLevel,
    LanguageSkill,
    Money,
    RateRange,
    RateUnit,
    SubjectRef,
    SubjectType,
    Workload,
    WorkLocationMode,
    WorkLocationPreference,
    WorkLocationRequirement,
)


class TestWorkload:
    def test_percentages_are_not_converted_without_a_known_full_time_week(self) -> None:
        workload = Workload(minimum_percentage=20, maximum_percentage=30, original_text="20-30%")

        assert not workload.is_convertible
        assert workload.hours_range() is None
        assert workload.percentage_range() == (20, 30)

    def test_percentages_convert_once_the_full_time_week_is_retained(self) -> None:
        workload = Workload(
            minimum_percentage=20,
            maximum_percentage=30,
            full_time_hours_per_week=42,
            original_text="20-30%",
        )

        assert workload.is_convertible
        assert workload.hours_range() == pytest.approx((8.4, 12.6))

    def test_hours_convert_back_into_percentages(self) -> None:
        workload = Workload(maximum_hours_per_week=21, full_time_hours_per_week=42)

        assert workload.percentage_range() == (None, 50)

    def test_open_ended_workload_keeps_only_what_normalizes_safely(self) -> None:
        workload = Workload(minimum_percentage=60, original_text="at least 60%")

        assert workload.percentage_range() == (60, None)
        assert workload.maximum_percentage is None

    def test_qualitative_workload_may_keep_the_original_text_alone(self) -> None:
        workload = Workload(original_text="negotiable")

        assert workload.percentage_range() is None
        assert workload.hours_range() is None

    def test_a_workload_must_retain_something(self) -> None:
        with pytest.raises(ValidationError, match="at least the original text"):
            Workload()

    def test_the_maximum_cannot_be_below_the_minimum(self) -> None:
        with pytest.raises(ValidationError, match="maximum percentage"):
            Workload(minimum_percentage=80, maximum_percentage=20)

    def test_percentages_stay_within_range(self) -> None:
        with pytest.raises(ValidationError):
            Workload(maximum_percentage=140)


class TestSubjectRef:
    def test_compact_form_round_trips(self) -> None:
        reference = SubjectRef.model_validate("person:salomon")

        assert reference.subject_type is SubjectType.person
        assert reference.subject_id == "salomon"
        assert reference.model_dump() == "person:salomon"

    def test_a_reference_without_a_prefix_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="person:<id>"):
            SubjectRef.model_validate("salomon")

    def test_an_unknown_subject_type_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SubjectRef.model_validate("team:delivery")


class TestGeoLocation:
    def test_country_codes_are_normalized(self) -> None:
        assert GeoLocation(country="ch", city="Zürich").country == "CH"

    def test_a_location_must_retain_at_least_one_field(self) -> None:
        with pytest.raises(ValidationError, match="at least one field"):
            GeoLocation()

    def test_a_location_may_be_only_the_text_the_source_used(self) -> None:
        assert GeoLocation(original_text="Raum Zürich / remote").country is None


class TestRates:
    def test_a_rate_range_must_use_one_currency(self) -> None:
        with pytest.raises(ValidationError, match="one currency"):
            RateRange(
                unit=RateUnit.hour,
                minimum=Money(amount=Decimal("120"), currency="CHF"),
                maximum=Money(amount=Decimal("140"), currency="EUR"),
            )

    def test_a_rate_range_may_be_open_at_the_top(self) -> None:
        rate = RateRange(
            unit=RateUnit.day,
            minimum=Money(amount=Decimal("1200"), currency="chf"),
            original_text="ab CHF 1200/Tag",
        )

        assert rate.minimum is not None
        assert rate.minimum.currency == "CHF"
        assert rate.maximum is None

    def test_amounts_keep_decimal_precision(self) -> None:
        assert Money(amount=Decimal("1200.50"), currency="CHF").amount == Decimal("1200.50")


class TestCredential:
    def test_a_credential_records_status_scope_and_validity(self) -> None:
        credential = Credential(
            id="iso-9001",
            kind=CredentialKind.certification,
            name="ISO 9001:2015",
            issuer="Example Certification AG",
            status=CredentialStatus.in_progress,
            scope="Industrial software engineering and consulting",
            valid_from=date(2026, 1, 1),
        )

        assert credential.status is CredentialStatus.in_progress
        assert credential.valid_until is None

    def test_a_credential_cannot_expire_before_it_starts(self) -> None:
        with pytest.raises(ValidationError, match="expire before"):
            Credential(
                id="iso-9001",
                kind=CredentialKind.certification,
                name="ISO 9001:2015",
                valid_from=date(2026, 1, 1),
                valid_until=date(2025, 1, 1),
            )

    def test_an_in_progress_credential_may_state_an_imprecise_expected_completion(self) -> None:
        degree = Credential(
            id="eth-bsc-mathematics",
            kind=CredentialKind.qualification,
            name="BSc Mathematics (D-MATH)",
            issuer="ETH Zürich",
            status=CredentialStatus.in_progress,
            expected_completion=DatePeriod(description="02/2027"),
        )

        assert degree.expected_completion is not None
        assert degree.expected_completion.start is None
        assert degree.valid_from is None

    def test_an_expected_completion_may_also_be_a_precise_date(self) -> None:
        credential = Credential(
            id="iso-27001",
            kind=CredentialKind.certification,
            name="ISO 27001:2022",
            status=CredentialStatus.in_progress,
            expected_completion=DatePeriod(end=date(2026, 10, 31)),
        )

        assert credential.expected_completion is not None
        assert credential.expected_completion.end == date(2026, 10, 31)

    @pytest.mark.parametrize(
        "status", [CredentialStatus.active, CredentialStatus.expired, CredentialStatus.withdrawn]
    )
    def test_a_settled_credential_cannot_expect_completion(
        self, status: CredentialStatus
    ) -> None:
        with pytest.raises(ValidationError, match="cannot have an expected completion"):
            Credential(
                id="iso-9001",
                kind=CredentialKind.certification,
                name="ISO 9001:2015",
                status=status,
                expected_completion=DatePeriod(description="02/2027"),
            )


    def test_a_credential_of_doubtful_currency_stays_unknown_with_its_doubt_recorded(self) -> None:
        accreditation = Credential(
            id="legacy-platform-accreditation",
            kind=CredentialKind.accreditation,
            name="Legacy platform integrator accreditation",
            status=CredentialStatus.unknown,
            notes="May not reflect current status; must not be presented as current.",
        )

        assert accreditation.status is CredentialStatus.unknown
        assert accreditation.notes is not None


class TestLanguageSkill:
    def test_a_level_may_be_qualified(self) -> None:
        skill = LanguageSkill(
            language="de",
            level=LanguageLevel.native,
            notes="Out of practice; spoken fluency is rusty.",
        )

        assert skill.level is LanguageLevel.native
        assert skill.notes is not None


class TestWorkLocationRequirement:
    def test_a_hybrid_arrangement_may_quantify_the_onsite_days(self) -> None:
        requirement = WorkLocationRequirement(
            mode=WorkLocationMode.hybrid,
            onsite_days_per_week=2,
            original_text="2 Tage/Woche vor Ort, Rest remote",
        )

        assert requirement.onsite_days_per_week == 2
        assert requirement.remote_share_percentage is None

    def test_a_hybrid_arrangement_need_not_quantify_anything(self) -> None:
        requirement = WorkLocationRequirement(
            mode=WorkLocationMode.hybrid,
            original_text="teilweise remote möglich",
        )

        assert requirement.onsite_days_per_week is None
        assert requirement.remote_share_percentage is None

    def test_remote_work_cannot_require_onsite_days(self) -> None:
        with pytest.raises(ValidationError, match="remote work cannot require on-site days"):
            WorkLocationRequirement(mode=WorkLocationMode.remote, onsite_days_per_week=2)

    def test_onsite_work_cannot_have_a_remote_share(self) -> None:
        with pytest.raises(ValidationError, match="on-site work cannot have a remote share"):
            WorkLocationRequirement(mode=WorkLocationMode.onsite, remote_share_percentage=40)

    def test_onsite_days_stay_within_a_week(self) -> None:
        with pytest.raises(ValidationError):
            WorkLocationRequirement(mode=WorkLocationMode.hybrid, onsite_days_per_week=9)


class TestOtherValues:
    def test_a_period_cannot_end_before_it_starts(self) -> None:
        with pytest.raises(ValidationError, match="end before it starts"):
            DatePeriod(start=date(2025, 5, 1), end=date(2025, 4, 1))

    def test_a_preferred_work_location_mode_must_be_accepted(self) -> None:
        with pytest.raises(ValidationError, match="preferred work location mode"):
            WorkLocationPreference(
                accepted_modes=(WorkLocationMode.remote,),
                preferred_mode=WorkLocationMode.onsite,
            )

    def test_work_location_preferences_need_at_least_one_accepted_mode(self) -> None:
        with pytest.raises(ValidationError):
            WorkLocationPreference(accepted_modes=())
