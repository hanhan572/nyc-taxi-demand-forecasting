"""Initial Streamlit dashboard for NYC Taxi Demand Forecasting.

Run from the repository root:
    streamlit run src/dashboard/app.py
"""

import sys
from pathlib import Path

import streamlit as st

# Make `src.dashboard...` importable no matter how the script is launched
# (streamlit run, Docker, or Streamlit's AppTest in CI).
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.dashboard.data_loader import (  # noqa: E402
    SAMPLE_DATA_LABEL,
    SAMPLE_ZONES,
    load_hourly_demand,
    summarize_zone,
)

st.set_page_config(page_title="NYC Taxi Demand Forecasting", layout="wide")
st.title("NYC Taxi Demand Forecasting")


@st.cache_data
def get_data():
    return load_hourly_demand(source="sample")


demand = get_data()

st.warning(SAMPLE_DATA_LABEL)

# Sidebar: zone selector
st.sidebar.header("Filters")
zone_ids = sorted(demand["location_id"].unique().tolist())
selected_zone = st.sidebar.selectbox(
    "Taxi zone",
    options=zone_ids,
    format_func=lambda z: f"{z} - {SAMPLE_ZONES.get(z, 'Unknown zone')}",
)

zone_df = demand[demand["location_id"] == selected_zone]
summary = summarize_zone(demand, selected_zone)

# Summary metrics
st.subheader(f"Zone {selected_zone}: {SAMPLE_ZONES.get(selected_zone, '')}")
col1, col2, col3 = st.columns(3)
col1.metric("Total pickups (sample)", f"{summary['total_pickups']:,}")
col2.metric(
    "Peak hour",
    summary["peak_hour"].strftime("%Y-%m-%d %H:00"),
    help=f"{summary['peak_pickups']} pickups in this hour",
)
col3.metric("Busiest hour of day", f"{summary['busiest_hour_of_day']:02d}:00")

# Line chart: hourly pickup demand
st.subheader("Hourly pickup demand")
st.line_chart(zone_df, x="hour", y="pickup_count")
st.caption(f"{summary['hours_covered']} hourly observations. Synthetic sample data.")

# Forecast placeholder (honest: not implemented yet)
st.subheader("Forecast")
st.info(
    "Forecasting integration coming soon. "
    "No forecasts are shown because the model is not connected yet."
)
