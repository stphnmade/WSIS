from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from wsis.core.config import get_settings
from wsis.core.weights import WEIGHT_STATE_KEYS, default_score_weights
from wsis.domain.models import CitySummary, ScoreWeights
from wsis.services.api_client import ApiCityClient


st.set_page_config(page_title="WSIS", layout="wide")


@st.cache_resource
def get_client() -> ApiCityClient:
    return ApiCityClient()


def build_weights() -> ScoreWeights:
    defaults = default_score_weights()
    st.sidebar.header("Score weights")
    affordability = st.sidebar.slider(
        "Affordability",
        0,
        100,
        int(defaults.affordability),
        5,
        key=WEIGHT_STATE_KEYS["affordability"],
    )
    job_market = st.sidebar.slider(
        "Job market",
        0,
        100,
        int(defaults.job_market),
        5,
        key=WEIGHT_STATE_KEYS["job_market"],
    )
    safety = st.sidebar.slider(
        "Safety",
        0,
        100,
        int(defaults.safety),
        5,
        key=WEIGHT_STATE_KEYS["safety"],
    )
    climate = st.sidebar.slider(
        "Climate",
        0,
        100,
        int(defaults.climate),
        5,
        key=WEIGHT_STATE_KEYS["climate"],
    )
    social_sentiment = st.sidebar.slider(
        "Social sentiment",
        0,
        100,
        int(defaults.social_sentiment),
        5,
        key=WEIGHT_STATE_KEYS["social_sentiment"],
    )

    return ScoreWeights(
        affordability=affordability,
        job_market=job_market,
        safety=safety,
        climate=climate,
        social_sentiment=social_sentiment,
    )


def build_map(cities: list[CitySummary]):
    settings = get_settings()
    frame = pd.DataFrame(
        [
            {
                "slug": city.slug,
                "city": city.name,
                "state": city.state_code,
                "score": city.overall_score,
                "latitude": city.latitude,
                "longitude": city.longitude,
                "headline": city.headline,
            }
            for city in cities
        ]
    )

    if settings.mapbox_token:
        px.set_mapbox_access_token(settings.mapbox_token)
        return px.scatter_mapbox(
            frame,
            lat="latitude",
            lon="longitude",
            color="score",
            size="score",
            hover_name="city",
            hover_data={"state": True, "headline": True, "latitude": False, "longitude": False},
            color_continuous_scale="YlGnBu",
            zoom=2.9,
            height=620,
            mapbox_style="carto-positron",
        )

    return px.scatter_geo(
        frame,
        lat="latitude",
        lon="longitude",
        color="score",
        size="score",
        hover_name="city",
        hover_data={"state": True, "headline": True},
        color_continuous_scale="YlGnBu",
        scope="usa",
        projection="albers usa",
        height=620,
    )


def open_profile(slug: str) -> None:
    st.session_state["selected_city_slug"] = slug
    st.switch_page("pages/1_City_Profile.py")


weights = build_weights()
client = get_client()
cities, source = client.list_cities(weights)

st.title("Where Should I Start")
st.caption(
    "Map-first relocation discovery for early-career movers. "
    f"Data source: {source}. Mapbox is optional; the app falls back to a native US map."
)

regions = ["All"] + sorted({city.region for city in cities})
selected_region = st.sidebar.selectbox("Region", regions)
filtered_cities = [city for city in cities if selected_region == "All" or city.region == selected_region]

top_city = filtered_cities[0]
score_average = round(sum(city.overall_score for city in filtered_cities) / len(filtered_cities), 2)

metric_columns = st.columns(3)
metric_columns[0].metric("Cities in view", len(filtered_cities))
metric_columns[1].metric("Top city right now", f"{top_city.name}, {top_city.state_code}")
metric_columns[2].metric("Average score", score_average)

st.plotly_chart(build_map(filtered_cities), use_container_width=True)

st.subheader("Shortlist")
table_frame = pd.DataFrame(
    [
        {
            "City": f"{city.name}, {city.state_code}",
            "Region": city.region,
            "Overall score": city.overall_score,
            "Affordability": city.score_breakdown.affordability,
            "Jobs": city.score_breakdown.job_market,
            "Safety": city.score_breakdown.safety,
            "Climate": city.score_breakdown.climate,
            "Social": city.score_breakdown.social_sentiment,
        }
        for city in filtered_cities
    ]
)
st.dataframe(table_frame, use_container_width=True, hide_index=True)

selected_city = st.selectbox(
    "Open a city profile",
    filtered_cities,
    format_func=lambda city: f"{city.name}, {city.state_code}",
)

profile_columns = st.columns([3, 2])
profile_columns[0].markdown(f"### {selected_city.name}, {selected_city.state_code}")
profile_columns[0].write(selected_city.headline)
profile_columns[1].metric("Livability score", selected_city.overall_score)

if st.button("View city profile", type="primary"):
    open_profile(selected_city.slug)

st.info(
    "TODO: upgrade this page to GeoPandas-backed choropleths and richer filtering "
    "once the normalized geography pipeline is in place."
)
