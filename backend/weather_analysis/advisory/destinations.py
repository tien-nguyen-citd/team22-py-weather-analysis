from dataclasses import dataclass, replace
from datetime import date

from sqlalchemy.orm import Session

from weather_analysis.advisory.activities import get_activity
from weather_analysis.advisory.candidates import add_months, format_month, month_window, parse_month
from weather_analysis.advisory.models import (
    ActivityProfile,
    DestinationRanking,
    DestinationRequest,
    DestinationResult,
    WeatherDay,
)
from weather_analysis.advisory.repository import AdvisoryWeatherRepository
from weather_analysis.advisory.scoring import (
    LOW_SUITABILITY_SCORE,
    SIMILAR_SCORE_GAP,
    ranking_key,
    score_candidates,
)
from weather_analysis.advisory.service import ADVICE_NOTES
from weather_analysis.repositories.location_repository import LocationRepository
from weather_analysis.services.climate_service import (
    ClimateClient,
    ClimateDataError,
    ClimatePeriod,
    calculate_climate_period,
    get_location_climate,
)


@dataclass(frozen=True)
class Destination:
    slug: str
    coastal: bool


DESTINATIONS: tuple[Destination, ...] = (
    Destination("sa-pa", False),
    Destination("ha-giang", False),
    Destination("moc-chau", False),
    Destination("ninh-binh", False),
    Destination("ha-noi", False),
    Destination("hue", False),
    Destination("da-lat", False),
    Destination("can-tho", False),
    Destination("ho-chi-minh", False),
    Destination("quang-ninh", True),
    Destination("da-nang", True),
    Destination("hoi-an", True),
    Destination("quy-nhon", True),
    Destination("nha-trang", True),
    Destination("phan-thiet", True),
    Destination("vung-tau", True),
    Destination("phu-quoc", True),
)


@dataclass(frozen=True)
class DestinationHistory:
    slug: str
    name: str
    region_label: str
    days: list[WeatherDay]


def normalize_destination_request(
    request: DestinationRequest, today: date
) -> tuple[date, ActivityProfile]:
    month = add_months(today, 1) if not request.month else parse_month(request.month)
    activity = get_activity(request.activity_id)
    return month, activity


def get_destination_ranking(
    session: Session,
    request: DestinationRequest,
    client: ClimateClient,
    today: date,
) -> DestinationRanking:
    month, activity = normalize_destination_request(request, today)
    period = calculate_climate_period(today)

    catalog = DESTINATIONS
    if activity.id == "beach":
        catalog = tuple(destination for destination in catalog if destination.coastal)

    histories: list[DestinationHistory] = []
    for destination in catalog:
        location = LocationRepository(session).find_by_slug(destination.slug)
        if location is None:
            continue
        get_location_climate(session, location, client, today)
        days = AdvisoryWeatherRepository(session).read_days(
            location.latitude,
            location.longitude,
            period.start_date,
            period.baseline_end,
        )
        histories.append(
            DestinationHistory(location.slug, location.name, location.region_label, days)
        )

    if not histories:
        raise ClimateDataError("Chưa có điểm đến nào trong danh mục")

    return build_destination_ranking(month, activity, histories, period)


def build_destination_ranking(
    month: date,
    activity: ActivityProfile,
    histories: list[DestinationHistory],
    period: ClimatePeriod,
) -> DestinationRanking:
    window = month_window(month)
    scored = sorted(
        (
            (
                history,
                score_candidates(
                    [window],
                    history.days,
                    period.start_date,
                    period.baseline_end,
                    activity,
                )[0],
            )
            for history in histories
        ),
        key=lambda item: ranking_key(item[1]),
    )
    best_score = scored[0][1].score
    destinations = [
        DestinationResult(
            slug=history.slug,
            name=history.name,
            region_label=history.region_label,
            candidate=replace(
                candidate,
                rank=index + 1,
                similar_to_best=index > 0
                and best_score - candidate.score < SIMILAR_SCORE_GAP,
            ),
        )
        for index, (history, candidate) in enumerate(scored)
    ]

    best = destinations[0]
    month_label = f"Tháng {month.month:02d}/{month.year:04d}"
    low_suitability = best.candidate.score < LOW_SUITABILITY_SCORE
    if low_suitability:
        summary = (
            f"Tháng này ít điểm đến phù hợp với {activity.name.lower()}. "
            f"{best.name} đứng đầu với {best.candidate.score:.1f}/100 điểm."
        )
    else:
        top_two = ", ".join(
            f"{item.name} ({item.candidate.score:.1f}/100)"
            for item in destinations[:2]
        )
        summary = f"{month_label} hợp với {activity.name.lower()} nhất: {top_two}."

    return DestinationRanking(
        month=format_month(month),
        activity=activity,
        baseline_start=period.start_date,
        baseline_end=period.baseline_end,
        destinations=destinations,
        summary=summary,
        low_suitability=low_suitability,
        notes=[
            *ADVICE_NOTES,
            "Chỉ xếp hạng trong danh sách điểm du lịch có sẵn, chưa gồm mọi địa điểm.",
        ],
    )
