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
st.info(detail.summary.score_context.explanation)
if detail.summary.score_context.beta_warning:
    st.warning(detail.summary.score_context.beta_warning)

metric_columns = st.columns(4)
metric_columns[0].metric("Livability score", detail.summary.overall_score)
metric_columns[1].metric("Median rent", f"${detail.metrics.median_rent:,.0f}")
metric_columns[2].metric("Median income", f"${detail.metrics.median_income:,.0f}")
metric_columns[3].metric("Population", f"{detail.metrics.population:,}")

breakdown_frame = pd.DataFrame(
    [
        {
            "category": dimension.label,
            "score": dimension.score,
            "included_in_score": "Yes" if dimension.included_in_score else "Context only",
            "confidence": dimension.confidence,
        }
        for dimension in detail.summary.score_dimensions
    ]
)

content_columns = st.columns([3, 2])
with content_columns[0]:
    st.subheader("Score breakdown")
    chart = px.bar(
        breakdown_frame,
        x="category",
        y="score",
        color="included_in_score",
        color_discrete_map={"Yes": "#2f7d62", "Context only": "#c3a373"},
        range_y=[0, 10],
    )
    st.plotly_chart(chart, use_container_width=True)
    st.caption(
        "Included in score: "
        + ", ".join(detail.summary.score_context.included_dimensions)
        + ". Context only: "
        + ", ".join(detail.summary.score_context.excluded_dimensions)
        + "."
    )

    st.subheader("Confidence and provenance")
    trust_frame = pd.DataFrame(
        [
            {
                "Dimension": dimension.label,
                "Confidence": dimension.confidence,
                "Included": "Yes" if dimension.included_in_score else "No",
                "Source": dimension.source,
                "Source date": dimension.source_date,
                "Imputed": "Yes" if dimension.is_imputed else "No",
            }
            for dimension in detail.summary.score_dimensions
        ]
    )
    st.dataframe(trust_frame, use_container_width=True, hide_index=True)

    st.subheader("Why this city might fit")
    for highlight in detail.highlights:
        st.write(f"- {highlight}")

with content_columns[1]:
    st.subheader("Social reality panel")
    st.metric("Reddit sentiment", detail.reddit_panel.sentiment_score)
    st.caption("Confidence: " + detail.reddit_panel.confidence + " | Included in score: No")
    st.write(detail.reddit_panel.summary)
    metadata_columns = st.columns(3)
    metadata_columns[0].metric("Posts analyzed", detail.reddit_panel.posts_analyzed)
    metadata_columns[1].metric("Lookback days", detail.reddit_panel.lookback_days)
    metadata_columns[2].metric("Generated", detail.reddit_panel.generated_at)
    st.caption(detail.reddit_panel.methodology)
    if detail.reddit_panel.provenance:
        st.caption("Provenance")
        for source in detail.reddit_panel.provenance:
            st.write(f"- {source.subreddit}: `{source.query}`")
            st.caption(source.note)
    for post in detail.reddit_panel.posts:
        st.markdown(f"**{post.title}**")
        st.write(post.excerpt)
        st.caption(f"Sentiment: {post.sentiment} | Source: {post.subreddit}")

st.info(
    "Reddit summaries are seeded beta context from structured local data. "
    "They stay visible in the profile, but they do not affect the ranked MVP score."
)
