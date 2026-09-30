from datetime import date
from typing import cast
from unittest.mock import patch

from sqlalchemy.orm import Session

from weather_analysis.models import Location
from weather_analysis.services.climate_service import ClimateClient, get_location_climates


def _location(slug: str, latitude: float, longitude: float) -> Location:
    return Location(
        name=slug,
        slug=slug,
        region_code="test",
        region_label="Test",
        temp_offset=0,
        latitude=latitude,
        longitude=longitude,
        pin_order=None,
    )


def test_multi_location_load_acquires_coordinate_locks_in_sorted_order() -> None:
    locations = [
        _location("north", 21, 105),
        _location("south", 10, 106),
        _location("same-as-south", 10, 106),
    ]
    with Session() as session, patch(
        "weather_analysis.services.climate_service.get_location_climate",
        return_value="loaded",
    ) as load:
        result = get_location_climates(
            session, locations, cast(ClimateClient, object()), date(2026, 9, 20)
        )

    assert list(result) == [(10, 106), (21, 105)]
    assert [(call.args[1].latitude, call.args[1].longitude) for call in load.call_args_list] == [
        (10, 106),
        (21, 105),
    ]
