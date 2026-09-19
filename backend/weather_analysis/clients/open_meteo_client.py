import math
from datetime import date, datetime, timedelta, timezone

import httpx
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError


VIETNAM_TIMEZONE = timezone(timedelta(hours=7))
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


class WeatherProviderError(Exception):
    """Không thể lấy dữ liệu hợp lệ từ nhà cung cấp thời tiết."""


class ArchiveDaily(BaseModel):
    time: list[str]
    precipitation_sum: list[float | None]
    temperature_2m_mean: list[float | None]


class OpenMeteoArchive(BaseModel):
    daily: ArchiveDaily


class _CurrentTemperature(BaseModel):
    temperature_2m: float | None = None


class _CurrentWeather(BaseModel):
    current: _CurrentTemperature | None = None


class _ForecastHourly(BaseModel):
    model_config = ConfigDict(extra="ignore")

    temperature_2m: list[float | None] = Field(min_length=24)
    apparent_temperature: list[float | None] = Field(min_length=24)
    precipitation_probability: list[float | None] = Field(min_length=24)
    precipitation: list[float | None] = Field(min_length=24)
    uv_index: list[float | None] = Field(min_length=24)
    relative_humidity_2m: list[float | None] = Field(min_length=24)
    wind_speed_10m: list[float | None] = Field(min_length=24)
    dew_point_2m: list[float | None] = Field(min_length=24)


class _ForecastDaily(BaseModel):
    model_config = ConfigDict(extra="ignore")

    time: list[date] = Field(min_length=7)
    sunrise: list[str | None] = Field(min_length=7)
    sunset: list[str | None] = Field(min_length=7)
    temperature_2m_max: list[float | None] = Field(min_length=7)
    temperature_2m_min: list[float | None] = Field(min_length=7)
    precipitation_sum: list[float | None] = Field(min_length=7)
    precipitation_probability_max: list[float | None] = Field(min_length=7)
    sunshine_duration: list[float | None] = Field(min_length=7)


class _ForecastResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hourly: _ForecastHourly
    daily: _ForecastDaily


class _AirQualityHourly(BaseModel):
    model_config = ConfigDict(extra="ignore")

    us_aqi: list[float | None]


class _AirQualityResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hourly: _AirQualityHourly


class OpenMeteoForecast(BaseModel):
    """Dữ liệu thô đã được kiểm tra và dùng để dựng dự báo."""

    hourly_temperature: list[float | None]
    hourly_apparent_temperature: list[float | None]
    hourly_rain_probability: list[float | None]
    hourly_precipitation: list[float | None]
    hourly_uv: list[float | None]
    hourly_humidity: list[float | None]
    hourly_wind: list[float | None]
    hourly_dew_point: list[float | None]
    daily_time: list[date]
    daily_sunrise: list[str | None]
    daily_sunset: list[str | None]
    daily_temp_max: list[float | None]
    daily_temp_min: list[float | None]
    daily_rain_sum: list[float | None]
    daily_rain_probability: list[float | None]
    daily_sunshine_duration: list[float | None]
    us_aqi: list[float | None] | None
    fetched_at: datetime


class OpenMeteoClient:
    def __init__(self, http_client: httpx.Client) -> None:
        self._http_client = http_client

    def fetch_current_temperatures(
        self, locations: list[tuple[str, float, float]]
    ) -> dict[str, float]:
        temperatures: dict[str, float] = {}
        for start in range(0, len(locations), 25):
            batch = locations[start : start + 25]
            try:
                response = self._http_client.get(
                    FORECAST_URL,
                    params={
                        "latitude": ",".join(str(item[1]) for item in batch),
                        "longitude": ",".join(str(item[2]) for item in batch),
                        "current": "temperature_2m",
                        "timezone": "Asia/Bangkok",
                    },
                )
                response.raise_for_status()
                payload: object = response.json()
                if len(batch) == 1 and isinstance(payload, dict):
                    items = [_CurrentWeather.model_validate(payload)]
                else:
                    items = TypeAdapter(list[_CurrentWeather]).validate_python(
                        payload
                    )
                if len(items) != len(batch):
                    raise ValueError("Invalid current temperatures response")
            except (httpx.HTTPError, ValidationError, ValueError) as error:
                raise WeatherProviderError(
                    "Không lấy được nhiệt độ hiện tại từ Open-Meteo"
                ) from error

            for (slug, _, _), item in zip(batch, items, strict=True):
                value = item.current.temperature_2m if item.current is not None else None
                if value is not None and math.isfinite(value):
                    temperatures[slug] = value
        return temperatures

    def fetch_archive(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> OpenMeteoArchive:
        try:
            response = self._http_client.get(
                ARCHIVE_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "daily": "precipitation_sum,temperature_2m_mean",
                    "timezone": "Asia/Bangkok",
                    "models": "era5",
                },
                timeout=45,
            )
            response.raise_for_status()
            return OpenMeteoArchive.model_validate(response.json())
        except (httpx.HTTPError, ValidationError, ValueError) as error:
            raise WeatherProviderError(
                "Không lấy được dữ liệu lịch sử từ Open-Meteo"
            ) from error

    def fetch_forecast(
        self,
        latitude: float,
        longitude: float,
    ) -> OpenMeteoForecast:
        try:
            response = self._http_client.get(
                FORECAST_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "hourly": (
                        "temperature_2m,apparent_temperature,"
                        "precipitation_probability,precipitation,uv_index,"
                        "relative_humidity_2m,wind_speed_10m,dew_point_2m"
                    ),
                    "daily": (
                        "sunrise,sunset,temperature_2m_max,temperature_2m_min,"
                        "precipitation_sum,precipitation_probability_max,"
                        "sunshine_duration"
                    ),
                    "forecast_days": 7,
                    "timezone": "Asia/Ho_Chi_Minh",
                },
            )
            response.raise_for_status()
            forecast = _ForecastResponse.model_validate(response.json())
        except (httpx.HTTPError, ValidationError, ValueError) as error:
            raise WeatherProviderError(
                "Không lấy được dữ liệu dự báo từ Open-Meteo"
            ) from error

        air_quality = self._fetch_air_quality(latitude, longitude)
        hourly = forecast.hourly
        daily = forecast.daily
        return OpenMeteoForecast(
            hourly_temperature=hourly.temperature_2m,
            hourly_apparent_temperature=hourly.apparent_temperature,
            hourly_rain_probability=hourly.precipitation_probability,
            hourly_precipitation=hourly.precipitation,
            hourly_uv=hourly.uv_index,
            hourly_humidity=hourly.relative_humidity_2m,
            hourly_wind=hourly.wind_speed_10m,
            hourly_dew_point=hourly.dew_point_2m,
            daily_time=daily.time,
            daily_sunrise=daily.sunrise,
            daily_sunset=daily.sunset,
            daily_temp_max=daily.temperature_2m_max,
            daily_temp_min=daily.temperature_2m_min,
            daily_rain_sum=daily.precipitation_sum,
            daily_rain_probability=daily.precipitation_probability_max,
            daily_sunshine_duration=daily.sunshine_duration,
            us_aqi=air_quality.hourly.us_aqi if air_quality is not None else None,
            fetched_at=datetime.now(VIETNAM_TIMEZONE),
        )

    def _fetch_air_quality(
        self,
        latitude: float,
        longitude: float,
    ) -> _AirQualityResponse | None:
        try:
            response = self._http_client.get(
                AIR_QUALITY_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "hourly": "us_aqi",
                    "timezone": "Asia/Ho_Chi_Minh",
                },
            )
            response.raise_for_status()
            return _AirQualityResponse.model_validate(response.json())
        except (httpx.HTTPError, ValidationError, ValueError):
            return None
