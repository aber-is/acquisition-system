"""Known, unknown and conflicting normalized values."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from acquisition.domain import (
    ExtractionMethod,
    ExtractionProvenance,
    NormalizedValue,
    ValueState,
)


def test_known_value_keeps_value_and_supporting_source() -> None:
    value = NormalizedValue[bool].known(
        True,
        source_text="B2B möglich",
        extraction=ExtractionProvenance(method=ExtractionMethod.rule_based, extractor="b2b-v1"),
    )

    assert value.is_known
    assert value.value is True
    assert value.source_text == "B2B möglich"
    assert value.extraction.method is ExtractionMethod.rule_based


def test_unknown_is_the_default_state() -> None:
    value = NormalizedValue[bool]()

    assert value.state is ValueState.unknown
    assert value.value is None
    assert not value.is_known
    assert value.extraction.method is ExtractionMethod.unknown


def test_unknown_value_may_retain_the_inconclusive_source_text() -> None:
    value = NormalizedValue[bool].unknown(source_text="Vertragsform nach Absprache")

    assert not value.is_known
    assert value.source_text == "Vertragsform nach Absprache"


def test_conflicting_value_retains_every_candidate() -> None:
    value = NormalizedValue[int].conflicting(60, 80, source_field="workload")

    assert value.state is ValueState.conflicting
    assert value.value is None
    assert value.candidates == (60, 80)


def test_known_value_requires_a_value() -> None:
    with pytest.raises(ValidationError, match="must carry a value"):
        NormalizedValue[int](state=ValueState.known)


def test_unknown_value_must_not_carry_a_value() -> None:
    with pytest.raises(ValidationError, match="only a known normalized value may carry a value"):
        NormalizedValue[int](state=ValueState.unknown, value=42)


def test_conflicting_value_needs_at_least_two_candidates() -> None:
    with pytest.raises(ValidationError, match="at least two candidates"):
        NormalizedValue[int].conflicting(60)


def test_candidates_are_reserved_for_conflicting_values() -> None:
    with pytest.raises(ValidationError, match="may carry candidates"):
        NormalizedValue[int](state=ValueState.unknown, candidates=(60, 80))


def test_values_are_validated_against_their_parameter() -> None:
    with pytest.raises(ValidationError):
        NormalizedValue[int].known("not a number")


def test_normalized_values_are_immutable() -> None:
    value = NormalizedValue[int].known(42)

    with pytest.raises(ValidationError):
        value.value = 43
