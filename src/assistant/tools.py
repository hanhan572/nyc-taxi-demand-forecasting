"""Deterministic taxi forecast query tools (synthetic demo data only)."""
from datetime import datetime
from zoneinfo import ZoneInfo

NY_TIMEZONE = ZoneInfo("America/New_York")

# These numbers are ILLUSTRATIVE MOCK forecasts, never model predictions.
MOCK_FORECASTS = [
    {"location_id": 161, "zone_name": "Midtown Center", "forecast_hour": "2026-11-23T18:00:00-05:00", "predicted_pickups": 120},
    {"location_id": 236, "zone_name": "Upper East Side North", "forecast_hour": "2026-11-23T18:00:00-05:00", "predicted_pickups": 85},
    {"location_id": 132, "zone_name": "JFK Airport", "forecast_hour": "2026-11-23T18:00:00-05:00", "predicted_pickups": 67},
    {"location_id": 161, "zone_name": "Midtown Center", "forecast_hour": "2026-11-23T19:00:00-05:00", "predicted_pickups": 110},
    {"location_id": 236, "zone_name": "Upper East Side North", "forecast_hour": "2026-11-23T19:00:00-05:00", "predicted_pickups": 92},
    {"location_id": 132, "zone_name": "JFK Airport", "forecast_hour": "2026-11-23T19:00:00-05:00", "predicted_pickups": 72},
]


def _validated_hour(forecast_hour: str) -> str:
    if not isinstance(forecast_hour, str):
        raise ValueError("forecast_hour must be an ISO-8601 datetime string with a time zone")
    try:
        parsed = datetime.fromisoformat(forecast_hour)
    except ValueError as exc:
        raise ValueError("forecast_hour must be ISO-8601, e.g. 2026-11-23T18:00:00-05:00") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("forecast_hour must specify a time zone offset")
    local = parsed.astimezone(NY_TIMEZONE)
    if local.minute or local.second or local.microsecond:
        raise ValueError("forecast_hour must be aligned to a whole hour")
    return local.isoformat()


def _validated_location_id(location_id: int) -> int:
    if isinstance(location_id, bool) or not isinstance(location_id, int) or location_id <= 0:
        raise ValueError("location_id must be a positive integer")
    return location_id


def get_forecast(location_id: int, forecast_hour: str) -> dict:
    """Return one zone/hour forecast or an explicit not-found result."""
    location_id = _validated_location_id(location_id)
    hour = _validated_hour(forecast_hour)
    for record in MOCK_FORECASTS:
        if record["location_id"] == location_id and record["forecast_hour"] == hour:
            return {"status": "ok", "source": "mock", **record.copy()}
    return {"status": "not_found", "source": "mock", "location_id": location_id,
            "forecast_hour": hour, "message": "No forecast is available for this zone and hour."}


def compare_zones(location_ids: list[int], forecast_hour: str) -> dict:
    """Compare 2–5 zone IDs without manufacturing unavailable forecasts."""
    if not isinstance(location_ids, list) or not 2 <= len(location_ids) <= 5:
        raise ValueError("location_ids must be a list containing 2 to 5 zone IDs")
    if len(set(str(item) for item in location_ids)) != len(location_ids):
        raise ValueError("location_ids must be unique")
    for location_id in location_ids:
        _validated_location_id(location_id)
    hour = _validated_hour(forecast_hour)
    results = [get_forecast(zone_id, hour) for zone_id in location_ids]
    available = sorted((row for row in results if row["status"] == "ok"),
                       key=lambda row: (-row["predicted_pickups"], row["location_id"]))
    missing = [row["location_id"] for row in results if row["status"] != "ok"]
    return {"status": "ok" if available else "not_found", "source": "mock",
            "forecast_hour": hour, "zones": available, "missing_location_ids": missing}


def get_high_demand_zones(forecast_hour: str, limit: int = 3) -> dict:
    """Rank sample zone forecasts for a selected hour."""
    hour = _validated_hour(forecast_hour)
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 10:
        raise ValueError("limit must be an integer from 1 to 10")
    rows = [record.copy() for record in MOCK_FORECASTS if record["forecast_hour"] == hour]
    rows.sort(key=lambda row: (-row["predicted_pickups"], row["location_id"]))
    return {"status": "ok" if rows else "not_found", "source": "mock",
            "forecast_hour": hour, "zones": rows[:limit]}
