"""Tests for the Streamlit dashboard (no database or API keys needed)."""

from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.dashboard.data_loader import (
    REQUIRED_COLUMNS,
    load_hourly_demand,
    summarize_zone,
    validate_demand,
)

APP_PATH = Path(__file__).resolve().parents[1] / "src" / "dashboard" / "app.py"


def test_sample_data_matches_contract():
    df = load_hourly_demand("sample")
    assert list(df.columns) == REQUIRED_COLUMNS
    assert pd.api.types.is_datetime64_any_dtype(df["hour"])
    assert not df.duplicated(subset=["location_id", "hour"]).any()
    assert (df["pickup_count"] >= 0).all()


def test_sample_data_is_deterministic():
    pd.testing.assert_frame_equal(
        load_hourly_demand("sample"), load_hourly_demand("sample")
    )


def test_validate_rejects_missing_column():
    with pytest.raises(ValueError):
        validate_demand(pd.DataFrame({"location_id": [1], "hour": [1]}))


def test_postgres_not_implemented_yet():
    with pytest.raises(NotImplementedError):
        load_hourly_demand("postgres")


def test_summarize_zone():
    df = pd.DataFrame(
        {
            "location_id": [161, 161, 237],
            "hour": pd.to_datetime(
                ["2025-01-01 08:00", "2025-01-01 09:00", "2025-01-01 08:00"]
            ),
            "pickup_count": [5, 12, 3],
        }
    )
    summary = summarize_zone(df, 161)
    assert summary["total_pickups"] == 17
    assert summary["peak_pickups"] == 12
    assert summary["peak_hour"] == pd.Timestamp("2025-01-01 09:00")


def test_app_runs_without_errors():
    at = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    assert not at.exception
    assert at.title[0].value == "NYC Taxi Demand Forecasting"
    assert len(at.sidebar.selectbox) == 1
    assert "coming soon" in at.info[0].value
