from __future__ import annotations

import html

import pandas as pd
import plotly.express as px
import streamlit as st

from wsis.core.weights import score_weights_from_state
from wsis.domain.models import CityDetail, ScoreWeights
from wsis.services.api_client import ApiCityClient
from wsis.ui.theme import inject_theme, render_metric_strip, render_page_header, render_pills
from wsis.ui.trust import city_core_freshness_summary, freshness_badge


st.set_page_config(page_title="WSIS | City Profile", layout="wide")


@st.cache_resource
def get_client() -> ApiCityClient:
    return ApiCityClient()


def current_weights() -> ScoreWeights:
    return score_weights_from_state(st.session_state)


def inject_profile_styles() -> None:
    inject_theme()
    st.markdown(
        """
        <style>
        .profile-hero {
            background: linear-gradient(120deg, rgba(232,244,255,0.94), rgba(223,248,238,0.92) 56%, rgba(255,240,184,0.76));
            border: 1px solid rgba(85, 119, 255, 0.16);
            border-radius: 24px;
            box-sizing: border-box;
            box-shadow: 0 18px 46px rgba(23, 33, 43, 0.07);
            margin-bottom: 1rem;
            padding: 1rem;
            max-width: 100%;
            overflow-wrap: anywhere;
        }
        .profile-hero h1 {
            font-size: clamp(2.15rem, 5vw, 4rem);
            margin-bottom: 0.2rem;
            overflow-wrap: anywhere;
        }
        .profile-copy {
            color: #53606b;
            font-size: 1rem;
            margin: 0.2rem 0 0.7rem;
            max-width: 58rem;
            overflow-wrap: anywhere;
        }
        .fit-note {
            border-left: 4px solid #ff7a6b;
            color: #53606b;
            margin: 0.65rem 0 0;
            padding-left: 0.72rem;
        }
        .trust-row {
            border-top: 1px solid #dce5e8;
            display: grid;
            gap: 0.8rem;
            grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.4fr) minmax(5.5rem, 0.55fr) minmax(4.5rem, 0.4fr);
            padding: 0.72rem 0;
            min-width: 0;
        }
        .trust-row:last-child {
            border-bottom: 1px solid #dce5e8;
        }
        .trust-title {
            color: #17212b;
            font-weight: 800;
            overflow-wrap: anywhere;
        }
        .trust-meta {
            color: #66717d;
            font-size: 0.86rem;
            min-width: 0;
            overflow-wrap: anywhere;
        }
        .social-quote {
            background: rgba(255,255,255,0.72);
            border: 1px solid rgba(255, 122, 107, 0.18);
            border-radius: 18px;
            box-sizing: border-box;
            padding: 0.9rem;
            max-width: 100%;
            overflow-wrap: anywhere;
        }
        @media (max-width: 900px) {
            [data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
                flex-wrap: wrap;
                gap: 1rem;
            }
            [data-testid="stColumn"] {
                flex: 1 1 100% !important;
                min-width: 0 !important;
                width: 100% !important;
            }
            .profile-hero {
                border-radius: 16px;
                padding: 0.82rem;
            }
            .profile-hero h1 {
                font-size: clamp(1.85rem, 11vw, 2.65rem);
                line-height: 1.02;
            }
            .wsis-mini-grid {
                grid-template-columns: repeat(auto-fit, minmax(min(100%, 8rem), 1fr));
            }
            .wsis-mini-value,
            .wsis-pill {
                overflow-wrap: anywhere;
                white-space: normal;
            }
            .trust-row {
                grid-template-columns: 1fr;
                gap: 0.25rem;
            }
            div[data-testid="stPlotlyChart"],
            div[data-testid="stPlotlyChart"] .js-plotly-plot,
            div[data-testid="stPlotlyChart"] .plot-container,
            div[data-testid="stPlotlyChart"] .svg-container {
                max-height: 300px !important;
                min-height: 0 !important;
            }
        }
        @media (max-width: 390px) {
            .profile-hero h1 {
                font-size: clamp(1.68rem, 10vw, 2.25rem);
            }
            .profile-copy {
                font-size: 0.94rem;
            }
            div[data-testid="stPlotlyChart"],
            div[data-testid="stPlotlyChart"] .js-plotly-plot,
            div[data-testid="stPlotlyChart"] .plot-container,
            div[data-testid="stPlotlyChart"] .svg-container {
                max-height: 270px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def trust_rows(detail: CityDetail) -> None:
    rows = []
    for dimension in detail.summary.score_dimensions:
        rows.append(
            f"""
            <div class="trust-row">
              <div>
                <div class="trust-title">{html.escape(dimension.label)}</div>
                <div class="trust-meta">{html.escape(dimension.confidence)}</div>
              </div>
              <div class="trust-meta">{html.escape(dimension.source)} · {html.escape(dimension.source_date)}</div>
              <div class="trust-meta">{html.escape(freshness_badge(dimension.source_date))}</div>
              <div class="trust-meta">{"Score" if dimension.included_in_score else "Context"}</div>
            </div>
            """
        )
    st.html("".join(rows))


def profile_badges(detail: CityDetail) -> list[str]:
    return [
        detail.summary.region,
        f"{detail.summary.score_context.overall_confidence.replace('_', ' ')} confidence",
        "Social context only",
    ]


inject_profile_styles()

client = get_client()
city_list, list_source = client.list_cities(current_weights())
default_slug = st.session_state.get("selected_city_slug", city_list[0].slug)

selected_slug = st.selectbox(
    "City",
    [city.slug for city in city_list],
    index=next((index for index, city in enumerate(city_list) if city.slug == default_slug), 0),
    format_func=lambda slug: next(
        f"{city.name}, {city.state_code}" for city in city_list if city.slug == slug
    ),
)
st.session_state["selected_city_slug"] = selected_slug

detail, source = client.get_city(selected_slug, current_weights())

st.html(
    f"""
    <div class="profile-hero">
      <div class="wsis-page-kicker">City Profile</div>
      <h1>{html.escape(detail.summary.name)}, {html.escape(detail.summary.state_code)}</h1>
      <div class="profile-copy">{html.escape(detail.summary.headline)}</div>
    </div>
    """,
)
render_pills(profile_badges(detail))
render_metric_strip(
    [
        ("WSIS score", f"{detail.summary.overall_score:.1f}"),
        ("Median rent", f"${detail.metrics.median_rent:,.0f}"),
        ("Median income", f"${detail.metrics.median_income:,.0f}"),
        ("Population", f"{detail.metrics.population:,}"),
    ]
)

if detail.summary.score_context.beta_warning:
    st.warning(detail.summary.score_context.beta_warning)

left, right = st.columns([1.35, 0.95], gap="large")
with left:
    render_page_header(
        "Score shape",
        "What is carrying the score?",
        detail.summary.score_context.explanation,
    )
    breakdown_frame = pd.DataFrame(
        [
            {
                "Category": dimension.label,
                "Score": dimension.score,
                "Role": "Score" if dimension.included_in_score else "Context",
            }
            for dimension in detail.summary.score_dimensions
        ]
    )
    chart = px.bar(
        breakdown_frame,
        x="Category",
        y="Score",
        color="Role",
        color_discrete_map={"Score": "#12a594", "Context": "#ff7a6b"},
        range_y=[0, 10],
    )
    chart.update_layout(
        height=340,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Plus Jakarta Sans", "color": "#22313d", "size": 13},
        margin={"l": 8, "r": 8, "t": 16, "b": 28},
        legend={
            "font": {"color": "#22313d", "size": 12},
            "title": {"font": {"color": "#22313d", "size": 12}},
        },
        xaxis={
            "tickangle": -25,
            "automargin": True,
            "tickfont": {"color": "#22313d", "size": 12},
            "title": {"font": {"color": "#22313d", "size": 12}},
        },
        yaxis={
            "automargin": True,
            "gridcolor": "rgba(34,49,61,0.22)",
            "linecolor": "rgba(34,49,61,0.38)",
            "tickfont": {"color": "#22313d", "size": 12},
            "title": {"font": {"color": "#22313d", "size": 12}},
        },
    )
    st.plotly_chart(chart, width="stretch")

    with st.container(border=True):
        st.subheader("Why it might fit")
        for highlight in detail.highlights:
            st.write(f"- {highlight}")

with right:
    with st.container(border=True):
        st.subheader("Social reality")
        st.metric("Sentiment", detail.reddit_panel.sentiment_score)
        st.caption(f"Confidence: {detail.reddit_panel.confidence} · Included in score: No")
        st.write(detail.reddit_panel.summary)
        render_metric_strip(
            [
                ("Posts", f"{detail.reddit_panel.posts_analyzed}"),
                ("Lookback", f"{detail.reddit_panel.lookback_days} days"),
                ("Generated", detail.reddit_panel.generated_at),
            ]
        )
        if detail.reddit_panel.posts:
            for post in detail.reddit_panel.posts[:2]:
                with st.container(border=True):
                    st.markdown(f"**{post.title}**")
                    st.write(post.excerpt)
                    st.caption(f"{post.sentiment} · {post.subreddit}")

st.markdown("---")
trust_left, trust_right = st.columns([1.25, 0.75], gap="large")
with trust_left:
    render_page_header(
        "Evidence",
        "Confidence ledger",
        "Each dimension keeps its confidence, source, freshness, and score role visible.",
    )
    trust_rows(detail)
with trust_right:
    with st.container(border=True):
        st.subheader("Core freshness")
        for item in city_core_freshness_summary(detail):
            st.write(f"- {item}")
        st.caption("Source names and dates stay in the ledger so the main profile stays readable.")
