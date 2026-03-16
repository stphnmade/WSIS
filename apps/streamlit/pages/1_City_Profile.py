from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from wsis.core.weights import score_weights_from_state
from wsis.domain.models import ScoreWeights
from wsis.services.api_client import ApiCityClient


st.set_page_config(page_title="WSIS | City Profile", layout="wide")


@st.cache_resource
def get_client() -> ApiCityClient:
    return ApiCityClient()


def current_weights() -> ScoreWeights:
    return score_weights_from_state(st.session_state)


client = get_client()
city_list, list_source = client.list_cities(current_weights())
default_slug = st.session_state.get("selected_city_slug", city_list[0].slug)

selected_slug = st.selectbox(
    "City",
    [city.slug for city in city_list],
    index=next(
        (index for index, city in enumerate(city_list) if city.slug == default_slug),
        0,
    ),
    format_func=lambda slug: next(
        f"{city.name}, {city.state_code}" for city in city_list if city.slug == slug
    ),
)
st.session_state["selected_city_slug"] = selected_slug

detail, source = client.get_city(selected_slug, current_weights())

st.title(f"{detail.summary.name}, {detail.summary.state_code}")
st.caption(f"Profile source: {source}. Discovery list source: {list_source}.")
st.write(detail.summary.headline)

metric_columns = st.columns(4)
metric_columns[0].metric("Livability score", detail.summary.overall_score)
metric_columns[1].metric("Median rent", f"${detail.metrics.median_rent:,.0f}")
metric_columns[2].metric("Median income", f"${detail.metrics.median_income:,.0f}")
metric_columns[3].metric("Population", f"{detail.metrics.population:,}")

breakdown_frame = pd.DataFrame(
    {"category": list(detail.summary.score_breakdown.as_dict().keys()), "score": list(detail.summary.score_breakdown.as_dict().values())}
)

content_columns = st.columns([3, 2])
with content_columns[0]:
    st.subheader("Score breakdown")
    chart = px.bar(
        breakdown_frame,
        x="category",
        y="score",
        color="score",
        color_continuous_scale="YlGnBu",
        range_y=[0, 10],
    )
    st.plotly_chart(chart, use_container_width=True)

    st.subheader("Why this city might fit")
    for highlight in detail.highlights:
        st.write(f"- {highlight}")

with content_columns[1]:
    st.subheader("Social reality panel")
    st.metric("Reddit sentiment", detail.reddit_panel.sentiment_score)
    st.write(detail.reddit_panel.summary)
    for post in detail.reddit_panel.posts:
        st.markdown(f"**{post.title}**")
        st.write(post.excerpt)
        st.caption(f"Sentiment: {post.sentiment}")

st.info(
    "TODO: replace the placeholder Reddit panel with a production service that "
    "stores vetted post summaries, provenance, and freshness metadata."
)
