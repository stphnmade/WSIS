from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from wsis.core.weights import score_weights_from_state
from wsis.services.api_client import ApiCityClient


st.set_page_config(page_title="WSIS | Comparison", layout="wide")


@st.cache_resource
def get_client() -> ApiCityClient:
    return ApiCityClient()


client = get_client()
active_weights = score_weights_from_state(st.session_state)
city_summaries, source = client.list_cities(active_weights)

seeded_slugs = st.session_state.get("comparison_selected_slugs", [])
default_slugs = [slug for slug in seeded_slugs if any(city.slug == slug for city in city_summaries)]
if len(default_slugs) < 2:
    default_slugs = [city.slug for city in city_summaries[:2]]
selected_slugs = st.multiselect(
    "Cities to compare",
    [city.slug for city in city_summaries],
    default=default_slugs,
    format_func=lambda slug: next(
        f"{city.name}, {city.state_code}" for city in city_summaries if city.slug == slug
    ),
)
st.session_state["comparison_selected_slugs"] = selected_slugs

st.title("City comparison")
st.caption(f"Comparison source: {source}. Select two to four cities.")
st.info(
    "Comparison ranking uses source-backed affordability, job market, safety, and climate. "
    "Social sentiment remains visible as context only."
)

if len(selected_slugs) < 2:
    st.warning("Select at least two cities to build a comparison.")
    st.stop()

details, detail_source = client.compare_cities(selected_slugs, active_weights)
st.caption(f"Detail source: {detail_source}.")

radar = go.Figure()
categories = [dimension.label for dimension in details[0].summary.score_dimensions]

for detail in details:
    values = [dimension.score for dimension in detail.summary.score_dimensions]
    radar.add_trace(
        go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=f"{detail.summary.name}, {detail.summary.state_code}",
        )
    )

radar.update_layout(
    polar={"radialaxis": {"visible": True, "range": [0, 10]}},
    showlegend=True,
    height=540,
)

st.plotly_chart(radar, use_container_width=True)

comparison_frame = pd.DataFrame(
    [
        {
            "City": f"{detail.summary.name}, {detail.summary.state_code}",
            "Overall score": detail.summary.overall_score,
            "Median rent": detail.metrics.median_rent,
            "Median home price": detail.metrics.median_home_price,
            "Median income": detail.metrics.median_income,
            "Job growth %": detail.metrics.job_growth_pct,
            "Unemployment %": detail.metrics.unemployment_pct,
        }
        for detail in details
    ]
)

st.subheader("Cost and market snapshot")
st.dataframe(comparison_frame, use_container_width=True, hide_index=True)

trust_frame = pd.DataFrame(
    [
        {
            "City": f"{detail.summary.name}, {detail.summary.state_code}",
            "Eligible for ranking": "Yes" if detail.summary.score_context.eligible_for_mvp_ranking else "No",
            "Included dimensions": ", ".join(detail.summary.score_context.included_dimensions),
            "Context only": ", ".join(detail.summary.score_context.excluded_dimensions),
            "Overall confidence": detail.summary.score_context.overall_confidence,
        }
        for detail in details
    ]
)
st.subheader("Trust summary")
st.dataframe(trust_frame, use_container_width=True, hide_index=True)

st.info(
    "This MVP comparison keeps social sentiment in view without letting seeded social context alter the rank."
)
