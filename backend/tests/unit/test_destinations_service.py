from datetime import date

import pytest
from sqlalchemy.orm import Session

from tests.advisory_helpers import FakeArchiveClient
from weather_analysis.advisory import destinations
from weather_analysis.advisory.destinations import Destination, get_destination_ranking
from weather_analysis.advisory.models import DestinationRequest
from weather_analysis.services.climate_service import ClimateDataError


TODAY = date(2026, 9, 20)


def test_first_call_fetches_history_and_second_call_reuses_it(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        destinations,
        "DESTINATIONS",
        (Destination("ha-noi", False), Destination("da-lat", False)),
    )
    client = FakeArchiveClient()
    first = get_destination_ranking(session, DestinationRequest(), client, TODAY)
    second = get_destination_ranking(session, DestinationRequest(), client, TODAY)

    assert first == second
    assert len(client.calls) == 2
    assert {item.slug for item in first.destinations} == {"ha-noi", "da-lat"}


def test_beach_activity_only_ranks_coastal_destinations(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        destinations,
        "DESTINATIONS",
        (Destination("ha-noi", False), Destination("da-nang", True)),
    )
    client = FakeArchiveClient()
    ranking = get_destination_ranking(
        session, DestinationRequest(activity_id="beach"), client, TODAY
    )

    assert [item.slug for item in ranking.destinations] == ["da-nang"]


def test_destination_missing_from_catalog_is_skipped(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        destinations,
        "DESTINATIONS",
        (Destination("ha-noi", False), Destination("khong-ton-tai", False)),
    )
    client = FakeArchiveClient()
    ranking = get_destination_ranking(session, DestinationRequest(), client, TODAY)

    assert [item.slug for item in ranking.destinations] == ["ha-noi"]


def test_raises_when_no_destination_has_data(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        destinations, "DESTINATIONS", (Destination("khong-ton-tai", False),)
    )
    client = FakeArchiveClient()

    with pytest.raises(ClimateDataError):
        get_destination_ranking(session, DestinationRequest(), client, TODAY)
