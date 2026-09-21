from collections.abc import Callable
import csv
from datetime import date

import pytest

from tests.advisory_helpers import make_history
from weather_analysis.advisory.activities import get_activity
from weather_analysis.advisory.candidates import month_window
from weather_analysis.advisory.destinations import (
    DESTINATIONS,
    DestinationHistory,
    build_destination_ranking,
    normalize_destination_request,
)
from weather_analysis.advisory.models import AdvisoryInputError, DestinationRequest
from weather_analysis.advisory.scoring import score_candidates
from weather_analysis.seed import LOCATIONS_SEED_PATH
from weather_analysis.services.climate_service import calculate_climate_period


TODAY = date(2026, 9, 20)
PERIOD = calculate_climate_period(TODAY)


def _history(slug: str, weather: Callable[[date], tuple[float, float]]) -> DestinationHistory:
    return DestinationHistory(slug, slug.title(), "Vùng test", make_history(PERIOD, weather))


def test_destinations_catalog_matches_seed_data_and_coastal_count() -> None:
    with LOCATIONS_SEED_PATH.open(encoding="utf-8-sig", newline="") as file:
        seed_slugs = {row["slug"] for row in csv.DictReader(file)}
    slugs = [destination.slug for destination in DESTINATIONS]
    assert len(slugs) == len(set(slugs)) == 17
    assert all(slug in seed_slugs for slug in slugs)
    assert sum(destination.coastal for destination in DESTINATIONS) == 8


def test_normalize_destination_request_defaults_to_next_month() -> None:
    month, activity = normalize_destination_request(DestinationRequest(), TODAY)
    assert month == date(2026, 10, 1)
    assert activity.id == "general"
    december_month, _ = normalize_destination_request(
        DestinationRequest(), date(2026, 12, 15)
    )
    assert december_month == date(2027, 1, 1)


@pytest.mark.parametrize(
    "request_",
    [
        DestinationRequest(month="2026-13"),
        DestinationRequest(month="2026-1"),
        DestinationRequest(activity_id="unknown"),
    ],
)
def test_normalize_destination_request_rejects_invalid_input(
    request_: DestinationRequest,
) -> None:
    with pytest.raises(AdvisoryInputError):
        normalize_destination_request(request_, TODAY)


def test_ranking_matches_direct_scoring_and_breaks_ties_by_history_order() -> None:
    activity = get_activity("travel")
    month = date(2027, 1, 1)
    histories = [
        _history("thap", lambda _: (45.0, 10.0)),
        _history("cao", lambda _: (24.0, 0.0)),
        _history("hoa-1", lambda _: (24.0, 0.0)),
    ]
    ranking = build_destination_ranking(month, activity, histories, PERIOD)
    expected = score_candidates(
        [month_window(month)],
        histories[1].days,
        PERIOD.start_date,
        PERIOD.baseline_end,
        activity,
    )[0]

    assert [item.candidate.rank for item in ranking.destinations] == [1, 2, 3]
    best, second, third = ranking.destinations
    assert best.slug == "cao"
    assert best.candidate.score == expected.score
    assert best.candidate.explanation == expected.explanation
    # "hoa-1" hòa điểm với "cao" nên giữ nguyên thứ tự trong danh sách histories.
    assert second.slug == "hoa-1"
    assert second.candidate.similar_to_best is True
    assert third.slug == "thap"
    assert third.candidate.similar_to_best is False


def test_summary_normal_and_low_suitability() -> None:
    activity = get_activity("beach")
    month = date(2026, 12, 1)
    good = build_destination_ranking(
        month,
        activity,
        [
            _history("phu-quoc", lambda _: (30.0, 0.0)),
            _history("vung-tau", lambda _: (29.0, 0.0)),
        ],
        PERIOD,
    )
    assert good.low_suitability is False
    assert good.summary.startswith("Tháng 12/2026 hợp với tắm biển nhất:")

    poor = build_destination_ranking(
        month,
        activity,
        [_history("phu-quoc", lambda _: (10.0, 20.0))],
        PERIOD,
    )
    assert poor.low_suitability is True
    assert poor.summary.startswith("Tháng này ít điểm đến phù hợp với tắm biển.")
    assert (
        "Chỉ xếp hạng trong danh sách điểm du lịch có sẵn" in poor.notes[-1]
    )
