from __future__ import annotations

import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from wsis.core.weights import score_weights_from_state
from wsis.domain.models import CityDetail
from wsis.services.api_client import ApiCityClient
from wsis.ui.theme import inject_theme, render_page_header, render_pills
from wsis.ui.trust import freshness_badge


st.set_page_config(page_title="WSIS | Comparison", layout="wide")


@st.cache_resource
def get_client() -> ApiCityClient:
    return ApiCityClient()


def inject_comparison_styles() -> None:
    inject_theme()
    st.markdown(
        """
        <style>
        .compare-card {
            background: rgba(255,255,255,0.78);
            border: 1px solid rgba(85,119,255,0.16);
            border-radius: 18px;
            box-sizing: border-box;
            box-shadow: 0 14px 36px rgba(23, 33, 43, 0.06);
            min-height: 18rem;
            padding: 0.95rem;
            max-width: 100%;
            overflow-wrap: anywhere;
        }
        .compare-card h3 {
            font-size: 1.25rem;
            line-height: 1.18;
            margin-bottom: 0.35rem;
            overflow-wrap: anywhere;
        }
        .compare-score {
            align-items: center;
            background: linear-gradient(120deg, rgba(223,248,238,0.95), rgba(255,240,184,0.72));
            border-radius: 14px;
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem 0.75rem;
            justify-content: space-between;
            margin: 0.55rem 0;
            padding: 0.65rem 0.75rem;
        }
        .compare-score span {
            color: #66717d;
            font-size: 0.75rem;
            font-weight: 850;
            text-transform: uppercase;
        }
        .compare-score strong {
            color: #17212b;
            font-size: 1.55rem;
        }
        .mini-table {
            border-top: 1px solid #dce5e8;
            margin-top: 0.75rem;
        }
        .mini-row {
            border-bottom: 1px solid #e5ecef;
            display: flex;
            flex-wrap: wrap;
            gap: 0.7rem;
            justify-content: space-between;
            padding: 0.58rem 0;
            min-width: 0;
        }
        .mini-row span {
            color: #66717d;
            flex: 1 1 6.5rem;
            min-width: 6.5rem;
            overflow-wrap: normal;
            word-break: normal;
        }
        .mini-row strong {
            color: #17212b;
            flex: 0 0 auto;
            min-width: max-content;
            overflow-wrap: normal;
            text-align: right;
            white-space: nowrap;
        }
        div[data-testid="stDataFrame"] {
            border-radius: 14px;
            overflow: hidden;
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
            .compare-card {
                min-height: auto;
            }
            .compare-card h3 {
                font-size: 1.1rem;
            }
            .wsis-mini-grid {
                grid-template-columns: repeat(auto-fit, minmax(min(100%, 8rem), 1fr));
            }
            .wsis-mini-value,
            .wsis-pill {
                overflow-wrap: anywhere;
                white-space: normal;
            }
            div[data-testid="stPlotlyChart"],
            div[data-testid="stPlotlyChart"] .js-plotly-plot,
            div[data-testid="stPlotlyChart"] .plot-container,
            div[data-testid="stPlotlyChart"] .svg-container {
                max-height: 320px !important;
                min-height: 0 !important;
            }
            div[data-testid="stDataFrame"] {
                max-width: 100%;
                overflow-x: auto;
            }
        }
        @media (max-width: 390px) {
            .mini-row {
                grid-template-columns: 1fr;
                gap: 0.2rem;
            }
            .mini-row strong {
                text-align: left;
            }
            div[data-testid="stPlotlyChart"],
            div[data-testid="stPlotlyChart"] .js-plotly-plot,
            div[data-testid="stPlotlyChart"] .plot-container,
            div[data-testid="stPlotlyChart"] .svg-container {
                max-height: 285px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def city_name(detail: CityDetail) -> str:
    return f"{detail.summary.name}, {detail.summary.state_code}"


def render_city_card(detail: CityDetail) -> None:
    st.html(
        f"""
        <div class="compare-card">
          <h3>{html.escape(city_name(detail))}</h3>
          <div class="compare-score">
            <span>WSIS score</span>
            <strong>{detail.summary.overall_score:.1f}</strong>
          </div>
          <div class="mini-table">
            <div class="mini-row"><span>Median rent</span><strong>${detail.metrics.median_rent:,.0f}</strong></div>
            <div class="mini-row"><span>Median income</span><strong>${detail.metrics.median_income:,.0f}</strong></div>
            <div class="mini-row"><span>Unemployment</span><strong>{detail.metrics.unemployment_pct:.1f}%</strong></div>
            <div class="mini-row"><span>Confidence</span><strong>{html.escape(detail.summary.score_context.overall_confidence.replace("_", " "))}</strong></div>
          </div>
        </div>
        """,
    )


def comparison_rows(details: list[CityDetail]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "City": city_name(detail),
                "Overall score": detail.summary.overall_score,
                "Median rent": detail.metrics.median_rent,
                "Median home price": detail.metrics.median_home_price,
                "Median income": detail.metrics.median_income,
                "Job growth %": detail.metrics.job_growth_pct,
                "Unemployment %": detail.metrics.unemployment_pct,
                "Home price freshness": freshness_badge(detail.metrics.median_home_price_source_date),
                "Job growth freshness": freshness_badge(detail.metrics.job_growth_source_date),
            }
            for detail in details
        ]
    )


def trust_rows(details: list[CityDetail]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "City": city_name(detail),
                "Eligible": "Yes" if detail.summary.score_context.eligible_for_mvp_ranking else "No",
                "Included": ", ".join(detail.summary.score_context.included_dimensions),
                "Context only": ", ".join(detail.summary.score_context.excluded_dimensions),
                "Confidence": detail.summary.score_context.overall_confidence,
                "Core freshness": ", ".join(
                    f"{dimension.label}: {freshness_badge(dimension.source_date)}"
                    for dimension in detail.summary.score_dimensions
                    if dimension.key in {"affordability", "job_market", "safety", "climate"}
                ),
            }
            for detail in details
        ]
    )


def quick_read_rows(details: list[CityDetail]) -> pd.DataFrame:
    top_city = max(details, key=lambda detail: detail.summary.overall_score)
    lowest_rent = min(details, key=lambda detail: detail.metrics.median_rent)
    strongest_job = min(details, key=lambda detail: detail.metrics.unemployment_pct)
    return pd.DataFrame(
        [
            {
                "Signal": "Top score",
                "City": city_name(top_city),
                "Value": f"{top_city.summary.overall_score:.1f}",
            },
            {
                "Signal": "Lowest rent",
                "City": city_name(lowest_rent),
                "Value": f"${lowest_rent.metrics.median_rent:,.0f}",
            },
            {
                "Signal": "Strong jobs",
                "City": city_name(strongest_job),
                "Value": f"{strongest_job.metrics.unemployment_pct:.1f}%",
            },
        ]
    )


inject_comparison_styles()

client = get_client()
active_weights = score_weights_from_state(st.session_state)
city_summaries, source = client.list_cities(active_weights)

render_page_header(
    "Comparison",
    "Line up your finalists.",
    "Pick a few cities and compare the practical tradeoffs before opening the deeper evidence tables.",
)

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
if len(selected_slugs) > 4:
    st.warning("Comparison is capped at four cities so the view stays readable.")
    selected_slugs = selected_slugs[:4]
st.session_state["comparison_selected_slugs"] = selected_slugs
st.caption("Social sentiment stays context-only; evidence details are below the charts.")

if len(selected_slugs) < 2:
    st.warning("Select at least two cities to build a comparison.")
    st.stop()

details, _ = client.compare_cities(selected_slugs, active_weights)
render_pills([f"{len(details)} cities", "Evidence visible", "Social context only"])

card_columns = st.columns(min(len(details), 4))
for column, detail in zip(card_columns, details):
    with column:
        render_city_card(detail)

st.markdown("---")
chart_left, chart_right = st.columns([1.15, 0.85], gap="large")

with chart_left:
    st.subheader("Score shape")
    radar = go.Figure()
    categories = [dimension.label for dimension in details[0].summary.score_dimensions]
    colors = ["#12a594", "#5577ff", "#ff7a6b", "#7d5fff"]

    for index, detail in enumerate(details):
        values = [dimension.score for dimension in detail.summary.score_dimensions]
        radar.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill="toself",
                name=city_name(detail),
                line={"color": colors[index % len(colors)], "width": 3},
                opacity=0.72,
            )
        )

    radar.update_layout(
        polar={
            "angularaxis": {"tickfont": {"color": "#22313d", "size": 12}},
            "radialaxis": {
                "visible": True,
                "range": [0, 10],
                "tickfont": {"color": "#22313d", "size": 11},
                "gridcolor": "rgba(34,49,61,0.22)",
                "linecolor": "rgba(34,49,61,0.42)",
            },
        },
        showlegend=True,
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Plus Jakarta Sans", "color": "#22313d"},
        margin={"l": 10, "r": 10, "t": 10, "b": 12},
        legend={"orientation": "h", "y": -0.08, "font": {"color": "#22313d", "size": 11}},
    )
    st.plotly_chart(radar, width="stretch")

with chart_right:
    with st.container(border=True):
        st.subheader("Quick read")
        st.dataframe(quick_read_rows(details), width="stretch", hide_index=True)
        st.caption("This read is a comparison aid, not a recommendation verdict.")

with st.expander("Cost and market table", expanded=True):
    st.dataframe(comparison_rows(details), width="stretch", hide_index=True)

with st.expander("Trust summary"):
    st.dataframe(trust_rows(details), width="stretch", hide_index=True)
