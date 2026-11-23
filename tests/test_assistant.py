"""Tests do not require network, API keys, PostgreSQL, or an ML model."""
import pytest
from src.assistant.agent import dispatch_tool
from src.assistant.tools import compare_zones, get_forecast, get_high_demand_zones

HOUR = "2026-11-23T18:00:00-05:00"


def test_single_forecast():
    row = get_forecast(161, HOUR)
    assert row["status"] == "ok"
    assert row["predicted_pickups"] == 120
    assert row["source"] == "mock"


def test_high_demand_ranking():
    rows = get_high_demand_zones(HOUR, limit=2)["zones"]
    assert [row["location_id"] for row in rows] == [161, 236]
    assert rows[0]["predicted_pickups"] >= rows[1]["predicted_pickups"]


def test_compare_zones_and_missing_records():
    result = compare_zones([132, 161], HOUR)
    assert [row["location_id"] for row in result["zones"]] == [161, 132]
    assert get_forecast(999, HOUR)["status"] == "not_found"


def test_input_validation():
    with pytest.raises(ValueError):
        get_forecast(-1, HOUR)
    with pytest.raises(ValueError):
        get_high_demand_zones("2026-11-23T18:30:00-05:00")
    with pytest.raises(ValueError):
        compare_zones([161, 161], HOUR)


def test_dispatch_rejects_invalid_tools():
    assert dispatch_tool("delete_database", {})["status"] == "error"
    assert dispatch_tool("get_forecast", {"location_id": -5, "forecast_hour": HOUR})["status"] == "error"
