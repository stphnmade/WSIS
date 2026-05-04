from __future__ import annotations

import html
import json
from urllib.request import urlopen

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from wsis.core.weights import WEIGHT_STATE_KEYS, default_score_weights, score_weights_from_state
from wsis.domain.models import CityDetail, ScoreWeights
from wsis.services.api_client import ApiCityClient
from wsis.ui.homepage import (
    active_filter_descriptions,
    aggregate_state_start_scores,
    apply_consumer_filters,
    badge_labels,
    best_places_to_start_score,
    city_reason_snippet,
    comparison_preview_rows,
    consumer_filter_labels,
    county_overlay_state_fips,
    interaction_stage_copy,
    labeled_city_slugs,
    map_focus_config,
    quick_stats,
    ranking_explanation,
    social_excerpt,
    social_preview_title,
    social_themes,
    standout_attribute,
    strongest_dimensions,
)
from wsis.ui.theme import inject_theme
from wsis.ui.trust import city_core_freshness_summary, freshness_badge


st.set_page_config(page_title="WSIS", layout="wide")


WEIGHT_LABELS = {
    "affordability": "Affordability",
    "job_market": "Job market",
    "safety": "Safety",
    "climate": "Climate",
}

COUNTY_GEOJSON_URL = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"

WEIGHT_HELP = {
    "affordability": "Lower cost pressure relative to income and home-value proxy.",
    "job_market": "Career upside from proxy job growth and unemployment conditions.",
    "safety": "Relative safety based on the current source crime-rate slice.",
    "climate": "Comfort score based on temperature and sunny-day inputs.",
}


@st.cache_resource
def get_client() -> ApiCityClient:
    return ApiCityClient()


@st.cache_data(show_spinner=False)
def load_county_geojson() -> dict[str, object] | None:
    try:
        with urlopen(COUNTY_GEOJSON_URL, timeout=8) as response:
            return json.load(response)
    except Exception:
        return None


@st.cache_data(show_spinner=False)
def filtered_county_geojson(state_fips_prefixes: tuple[str, ...]) -> dict[str, object] | None:
    if not state_fips_prefixes:
        return None
    county_geojson = load_county_geojson()
    if county_geojson is None:
        return None

    features = [
        feature
        for feature in county_geojson.get("features", [])
        if str(feature.get("id", ""))[:2] in state_fips_prefixes
    ]
    if not features:
        return None

    return {
        "type": county_geojson.get("type", "FeatureCollection"),
        "features": features,
    }


def inject_styles() -> None:
    inject_theme()
    st.markdown(
        """
        <style>
        .wsis-eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.09em;
            font-size: 0.78rem;
            color: #12a594;
            font-weight: 850;
        }
        .wsis-hero {
            background:
                linear-gradient(120deg, rgba(223, 248, 238, 0.96), rgba(232, 244, 255, 0.92) 58%, rgba(255, 240, 184, 0.82));
            border: 1px solid rgba(18, 165, 148, 0.18);
            border-radius: 24px;
            box-shadow: 0 20px 56px rgba(23, 33, 43, 0.08);
            padding: 1.15rem 1.25rem;
            margin-bottom: 0.75rem;
        }
        .wsis-hero h1 {
            font-family: "Fraunces", "Plus Jakarta Sans", serif;
            font-size: clamp(2rem, 4vw, 3.7rem);
            line-height: 0.98;
            margin: 0.2rem 0 0.55rem 0;
            color: #17212b;
        }
        .wsis-hero p {
            font-size: 1rem;
            color: #51606b;
            margin-bottom: 0.3rem;
            max-width: 58rem;
        }
        .wsis-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin: 0.45rem 0 0.1rem 0;
        }
        .wsis-chip {
            display: inline-block;
            padding: 0.32rem 0.68rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(18, 165, 148, 0.2);
            color: #21413d;
            font-size: 0.8rem;
            font-weight: 750;
        }
        .wsis-note {
            border-left: 3px solid #ff7a6b;
            padding-left: 0.75rem;
            margin-top: 0.55rem;
            color: #51606b;
        }
        .wsis-placeholder {
            border: 1px dashed rgba(85, 119, 255, 0.34);
            border-radius: 16px;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.68);
            min-height: 150px;
        }
        .wsis-placeholder h4 {
            margin: 0 0 0.45rem 0;
            color: #17212b;
        }
        .wsis-placeholder p {
            color: #56616c;
            margin-bottom: 0.65rem;
        }
        .wsis-mini {
            font-size: 0.86rem;
            color: #66717d;
        }
        .wsis-section-space {
            padding-top: 0.15rem;
        }
        .wsis-map-shell {
            border: 1px solid rgba(85, 119, 255, 0.14);
            border-radius: 22px;
            background: rgba(255,255,255,0.78);
            box-shadow: 0 16px 40px rgba(23, 33, 43, 0.06);
            padding: 0.85rem;
        }
        .wsis-tray {
            border: 1px solid rgba(18, 165, 148, 0.18);
            border-radius: 18px;
            background: rgba(255,255,255,0.82);
            padding: 0.8rem;
        }
        .wsis-tray-compact {
            border: 1px solid rgba(85, 119, 255, 0.16);
            border-radius: 16px;
            background: rgba(248, 252, 255, 0.94);
            padding: 0.7rem 0.8rem;
            margin-top: 0.55rem;
        }
        .wsis-state-bar {
            border: 1px solid rgba(18, 165, 148, 0.14);
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.82);
            padding: 0.75rem 0.85rem;
            margin-bottom: 0.7rem;
        }
        .wsis-selected-callout {
            border: 1px solid rgba(255, 122, 107, 0.28);
            background: linear-gradient(135deg, rgba(255, 240, 184, 0.72), rgba(232, 244, 255, 0.84));
            border-radius: 16px;
            padding: 0.8rem;
            margin-bottom: 0.8rem;
        }
        .wsis-decision-cta {
            align-items: center;
            background: rgba(255,255,255,0.82);
            border: 1px solid rgba(18, 165, 148, 0.18);
            border-radius: 18px;
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            margin: 0.75rem 0 0.25rem;
            padding: 0.85rem 1rem;
        }
        .wsis-decision-cta strong {
            color: #17212b;
        }
        .wsis-decision-cta span {
            color: #66717d;
            display: block;
            font-size: 0.9rem;
        }
        .wsis-compact-card {
            background: rgba(255,255,255,0.82);
            border: 1px solid rgba(18, 165, 148, 0.18);
            border-radius: 18px;
            box-shadow: 0 14px 34px rgba(23, 33, 43, 0.06);
            margin-bottom: 0.6rem;
            padding: 0.9rem;
        }
        .wsis-card-rank {
            color: #66717d;
            font-size: 0.78rem;
            font-weight: 800;
            text-transform: uppercase;
        }
        .wsis-card-title {
            color: #17212b;
            font-size: clamp(1.35rem, 2.4vw, 2rem);
            font-weight: 850;
            line-height: 1.08;
            margin: 0.18rem 0 0.55rem;
        }
        .wsis-stat-row {
            display: grid;
            gap: 0.5rem;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            margin: 0.7rem 0;
        }
        .wsis-stat {
            background: #f8fcff;
            border: 1px solid rgba(85, 119, 255, 0.12);
            border-radius: 12px;
            padding: 0.55rem 0.6rem;
        }
        .wsis-stat-label {
            color: #66717d;
            font-size: 0.68rem;
            font-weight: 850;
            text-transform: uppercase;
        }
        .wsis-stat-value {
            color: #17212b;
            font-size: 1.05rem;
            font-weight: 850;
            margin-top: 0.08rem;
        }
        .wsis-card-copy {
            color: #26323d;
            font-size: 0.94rem;
            line-height: 1.45;
            margin: 0.55rem 0 0;
        }
        .wsis-muted-copy {
            color: #66717d;
            font-size: 0.88rem;
            line-height: 1.45;
            margin-top: 0.35rem;
        }
        .wsis-side-note {
            color: #66717d;
            font-size: 0.94rem;
            line-height: 1.5;
            margin: 0.4rem 0 0.65rem;
        }
        div.stButton > button,
        div[data-testid="stBaseButton-secondary"],
        div[data-testid="stPopover"] button,
        div[data-testid="stPageLink"] a {
            background: #ffffff !important;
            border: 1px solid rgba(18, 165, 148, 0.28) !important;
            border-radius: 999px !important;
            color: #12322f !important;
            font-weight: 800 !important;
            line-height: 1.15 !important;
            min-height: 2.75rem !important;
            overflow-wrap: normal !important;
            white-space: nowrap !important;
        }
        div.stButton > button:disabled {
            background: #f3f7f8 !important;
            color: #70808b !important;
            opacity: 1 !important;
        }
        div[data-testid="stPopover"] button p,
        div.stButton > button p {
            color: inherit !important;
            overflow-wrap: normal !important;
            white-space: nowrap !important;
        }
        @media (max-width: 900px) {
            .block-container {
                padding-left: 0.85rem;
                padding-right: 0.85rem;
            }
            .wsis-hero {
                border-radius: 18px;
                padding: 0.95rem;
            }
            .wsis-hero h1 {
                font-size: clamp(1.85rem, 10vw, 2.45rem);
                line-height: 1.02;
            }
            .wsis-hero p {
                font-size: 0.95rem;
            }
            .wsis-chip-row {
                gap: 0.38rem;
            }
            .wsis-chip {
                max-width: 100%;
                overflow-wrap: anywhere;
                padding: 0.34rem 0.58rem;
            }
            .wsis-note {
                padding-left: 0.6rem;
            }
            .wsis-map-shell {
                border-radius: 16px;
                padding: 0.55rem;
            }
            .wsis-tray,
            .wsis-tray-compact,
            .wsis-state-bar,
            .wsis-selected-callout,
            .wsis-decision-cta {
                border-radius: 14px;
                padding: 0.7rem;
            }
            .wsis-tray-compact {
                margin-top: 0.45rem;
            }
            .wsis-placeholder {
                min-height: 0;
                padding: 0.85rem;
            }
            .wsis-decision-cta {
                align-items: stretch;
                flex-direction: column;
                gap: 0.65rem;
            }
            .wsis-stat-row {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            div[data-testid="stButton"] button,
            div[data-testid="stBaseButton-secondary"] button,
            div[data-testid="stPopover"] button {
                min-height: 2.75rem;
                white-space: nowrap;
                line-height: 1.18;
            }
            div[data-testid="stMetric"] {
                overflow-wrap: anywhere;
            }
            div[data-testid="stPlotlyChart"] {
                max-width: 100%;
                overflow: hidden;
            }
            div[data-testid="stPlotlyChart"] .js-plotly-plot,
            div[data-testid="stPlotlyChart"] .plot-container,
            div[data-testid="stPlotlyChart"] .svg-container {
                height: 390px !important;
                min-height: 390px !important;
            }
            div[data-testid="stPlotlyChart"] .main-svg {
                height: 390px !important;
                max-width: 100% !important;
            }
        }
        @media (max-width: 390px) {
            .block-container {
                padding-left: 0.7rem;
                padding-right: 0.7rem;
            }
            .wsis-hero {
                padding: 0.85rem;
            }
            .wsis-map-shell {
                padding: 0.45rem;
            }
            div[data-testid="stPlotlyChart"] .js-plotly-plot,
            div[data-testid="stPlotlyChart"] .plot-container,
            div[data-testid="stPlotlyChart"] .svg-container,
            div[data-testid="stPlotlyChart"] .main-svg {
                height: 345px !important;
                min-height: 345px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_state() -> None:
    defaults = default_score_weights()
    default_values = defaults.model_dump()
    for weight_name, state_key in WEIGHT_STATE_KEYS.items():
        st.session_state.setdefault(state_key, int(default_values[weight_name]))
    st.session_state.setdefault("home_region", "All")
    st.session_state.setdefault("home_compare_slugs", [])
    st.session_state.setdefault("home_selected_filters", [])
    st.session_state.setdefault("selected_city_slug", "")
    st.session_state.setdefault("home_compare_notice", "")


def current_weights() -> ScoreWeights:
    return score_weights_from_state(st.session_state)


def render_section_header(title: str, eyebrow: str, description: str) -> None:
    st.html(f'<div class="wsis-eyebrow">{html.escape(eyebrow)}</div>')
    st.subheader(title)
    st.caption(description)


def render_badges(labels: list[str]) -> None:
    if not labels:
        return
    chips = "".join(
        f'<span class="wsis-chip">{html.escape(label)}</span>' for label in labels
    )
    st.html(f'<div class="wsis-chip-row">{chips}</div>')


def placeholder_card(title: str, body: str, footer: str) -> None:
    st.html(
        f"""
        <div class="wsis-placeholder">
          <h4>{html.escape(title)}</h4>
          <p>{html.escape(body)}</p>
          <div class="wsis-mini">{html.escape(footer)}</div>
        </div>
        """,
    )


def compact_stats_html(items: list[tuple[str, str]]) -> str:
    cells = []
    for label, value in items[:3]:
        cells.append(
            f"""
            <div class="wsis-stat">
              <div class="wsis-stat-label">{html.escape(label)}</div>
              <div class="wsis-stat-value">{html.escape(value)}</div>
            </div>
            """
        )
    return '<div class="wsis-stat-row">' + "".join(cells) + "</div>"


def open_profile(slug: str) -> None:
    st.session_state["selected_city_slug"] = slug
    st.switch_page("pages/1_City_Profile.py")


def open_comparison() -> None:
    st.session_state["comparison_selected_slugs"] = st.session_state["home_compare_slugs"]
    st.switch_page("pages/2_Comparison.py")


def fetch_city_details(
    client: ApiCityClient,
    slugs: list[str],
    weights: ScoreWeights,
) -> tuple[list[CityDetail], str]:
    slug_list = list(dict.fromkeys(slugs))
    if not slug_list:
        return [], "local fallback"
    if len(slug_list) == 1:
        detail, source = client.get_city(slug_list[0], weights)
        return [detail], source
    details, source = client.compare_cities(slug_list, weights)
    return details, source


def current_compare_selection(available_slugs: set[str]) -> list[str]:
    return [slug for slug in st.session_state["home_compare_slugs"] if slug in available_slugs][:3]


def toggle_compare_city(slug: str, available_slugs: set[str]) -> None:
    selected = current_compare_selection(available_slugs)
    if slug in selected:
        selected.remove(slug)
    elif len(selected) < 3:
        selected.append(slug)
    else:
        st.session_state["home_compare_notice"] = "Comparison is limited to three cities on Home."
    st.session_state["home_compare_slugs"] = selected


def update_selected_city(slug: str) -> None:
    st.session_state["selected_city_slug"] = slug


def clear_selected_city() -> None:
    st.session_state["selected_city_slug"] = ""


def reset_discovery_tray() -> None:
    clear_selected_city()
    st.session_state["home_region"] = "All"
    st.session_state["home_selected_filters"] = []
    clear_compare_selection()
    st.session_state["home_compare_notice"] = ""


def clear_compare_selection() -> None:
    st.session_state["home_compare_slugs"] = []


def _focus_city_frame(
    city_frame: pd.DataFrame,
    label_slugs: set[str],
    focus_mode: str,
) -> pd.DataFrame:
    if city_frame.empty:
        return city_frame

    if focus_mode in {"inspect", "compare"}:
        return city_frame.copy()

    if focus_mode == "region":
        population_cutoff = city_frame["population"].quantile(0.55)
        return city_frame[
            (city_frame["population"] >= population_cutoff)
            | city_frame["slug"].isin(label_slugs)
        ].copy()

    return city_frame[city_frame["slug"].isin(label_slugs)].copy()


def _label_city_frame(
    focus_frame: pd.DataFrame,
    label_slugs: set[str],
    focus_mode: str,
) -> pd.DataFrame:
    if focus_frame.empty:
        return focus_frame

    if focus_mode in {"inspect", "compare"}:
        population_cutoff = focus_frame["population"].quantile(0.6)
        labeled = focus_frame[
            (focus_frame["population"] >= population_cutoff)
            | focus_frame["slug"].isin(label_slugs)
        ].copy()
        labeled.loc[labeled["label"] == "", "label"] = (
            labeled["city"] + ", " + labeled["state_code"]
        )
        return labeled

    return focus_frame[focus_frame["slug"].isin(label_slugs)].copy()


def _glimmer_sizes(city_frame: pd.DataFrame, focus_mode: str) -> list[float]:
    if city_frame.empty:
        return []

    min_population = float(city_frame["population"].min())
    max_population = float(city_frame["population"].max())
    population_span = max(max_population - min_population, 1.0)
    mode_boost = {
        "national": 0.0,
        "region": 1.3,
        "compare": 2.4,
        "inspect": 2.8,
    }.get(focus_mode, 0.0)

    sizes: list[float] = []
    for row in city_frame.itertuples():
        population_ratio = (float(row.population) - min_population) / population_span
        sizes.append(round(7.0 + (population_ratio * 9.5) + (float(row.start_score) * 0.22) + mode_boost, 2))
    return sizes


def _focus_marker_sizes(city_frame: pd.DataFrame, focus_mode: str) -> list[float]:
    if city_frame.empty:
        return []

    base_size = {
        "national": 8.5,
        "region": 10.5,
        "compare": 13.0,
        "inspect": 14.5,
    }.get(focus_mode, 10.0)
    return [round(base_size + (float(score) * 0.75), 2) for score in city_frame["start_score"]]


def build_map(
    details: list[CityDetail],
    weights: ScoreWeights,
    selected_region: str,
    selected_detail: CityDetail | None,
    compare_details: list[CityDetail],
):
    focus = map_focus_config(selected_region, selected_detail, compare_details)
    label_slugs = labeled_city_slugs(
        details,
        weights,
        selected_region,
        selected_detail,
        compare_details,
    )
    state_rows = aggregate_state_start_scores(details, weights)
    state_frame = pd.DataFrame(state_rows)
    focus_mode = str(focus["mode"])
    city_frame = pd.DataFrame(
        [
            {
                "slug": detail.summary.slug,
                "city": detail.summary.name,
                "state": detail.summary.state,
                "state_code": detail.summary.state_code,
                "population": detail.summary.population,
                "score": detail.summary.overall_score,
                "start_score": best_places_to_start_score(detail, weights),
                "latitude": detail.summary.latitude,
                "longitude": detail.summary.longitude,
                "standout": standout_attribute(detail),
                "label": f"{detail.summary.name}, {detail.summary.state_code}"
                if detail.summary.slug in label_slugs
                else "",
            }
            for detail in details
        ]
    )
    county_state_fips = ()
    if focus_mode in {"inspect", "compare"}:
        county_state_fips = tuple(
            sorted(
                county_overlay_state_fips(
                    details,
                    selected_region,
                    selected_detail,
                    compare_details,
                )
            )
        )
    county_geojson = filtered_county_geojson(county_state_fips)
    focus_frame = _focus_city_frame(city_frame, label_slugs, focus_mode).reset_index(drop=True)
    labeled_frame = _label_city_frame(focus_frame, label_slugs, focus_mode)
    figure = go.Figure()
    figure.add_trace(
        go.Choropleth(
            locations=state_frame["state_code"],
            z=state_frame["start_score"],
            locationmode="USA-states",
            text=state_frame["state"],
            customdata=state_frame[["top_city", "city_count"]],
            colorscale=[
                [0.0, "#fff0b8"],
                [0.42, "#8ee6d6"],
                [0.72, "#5bb6ff"],
                [1.0, "#7d5fff"],
            ],
            zmin=0,
            zmax=10,
            showscale=True,
            colorbar={
                "title": "Start",
                "len": 0.68,
                "thickness": 14,
            },
            marker_line_color="rgba(255,255,255,0.92)",
            marker_line_width=1.35,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Best places to start: %{z:.1f}/10<br>"
                "Cities tracked: %{customdata[1]}<br>"
                "Top local starting point: %{customdata[0]}"
                "<extra></extra>"
            ),
        )
    )
    if county_geojson is not None:
        county_ids = [
            feature.get("id")
            for feature in county_geojson.get("features", [])
            if feature.get("id")
        ]
        figure.add_trace(
            go.Choropleth(
                geojson=county_geojson,
                locations=county_ids,
                z=[0] * len(county_ids),
                featureidkey="id",
                colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                marker_line_color="rgba(94, 104, 105, 0.18)",
                marker_line_width=0.35,
                showscale=False,
                hoverinfo="skip",
            )
        )

    selected_slug = selected_detail.summary.slug if selected_detail is not None else None
    selected_points = city_frame.index[city_frame["slug"] == selected_slug].tolist() if selected_slug else []
    halo_sizes = _glimmer_sizes(city_frame, focus_mode)
    figure.add_trace(
        go.Scattergeo(
            lat=city_frame["latitude"],
            lon=city_frame["longitude"],
            hovertext=[f"{row.city}, {row.state}" for row in city_frame.itertuples()],
            customdata=city_frame[["slug", "state", "start_score", "score", "standout"]],
            mode="markers",
            marker={
                "size": halo_sizes,
                "color": "rgba(18, 165, 148, 0.18)",
                "opacity": 1.0,
                "line": {"color": "rgba(18, 165, 148, 0.0)", "width": 0},
                "showscale": False,
            },
            selectedpoints=selected_points or None,
            selected={"marker": {"opacity": 1.0, "size": max(halo_sizes or [10]) + 4, "color": "rgba(18, 165, 148, 0.36)"}},
            unselected={"marker": {"opacity": 1.0}},
            hovertemplate=(
                "<b>%{hovertext}</b><br>"
                "Potential fit glimmer: %{customdata[2]:.1f}/10<br>"
                "Tap to inspect this city"
                "<extra></extra>"
            ),
            showlegend=False,
        )
    )
    figure.add_trace(
        go.Scattergeo(
            lat=city_frame["latitude"],
            lon=city_frame["longitude"],
            hoverinfo="skip",
            mode="markers",
            marker={
                "size": [round(size * 0.44, 2) for size in halo_sizes],
                "color": "rgba(255,255,255,0.86)",
                "opacity": 1.0,
                "line": {"color": "rgba(255,255,255,0.0)", "width": 0},
                "showscale": False,
            },
            showlegend=False,
        )
    )
    if not focus_frame.empty:
        focus_selected_points = (
            focus_frame.index[focus_frame["slug"] == selected_slug].tolist() if selected_slug else []
        )
        focus_sizes = _focus_marker_sizes(focus_frame, focus_mode)
        figure.add_trace(
            go.Scattergeo(
                lat=focus_frame["latitude"],
                lon=focus_frame["longitude"],
                hovertext=[f"{row.city}, {row.state}" for row in focus_frame.itertuples()],
                customdata=focus_frame[["slug", "state", "start_score", "score", "standout"]],
                mode="markers",
                marker={
                    "size": focus_sizes,
                    "color": focus_frame["start_score"],
                    "colorscale": [
                        [0.0, "#ffcf70"],
                        [0.45, "#12a594"],
                        [0.75, "#5577ff"],
                        [1.0, "#ff7a6b"],
                    ],
                    "cmin": 0,
                    "cmax": 10,
                    "opacity": 0.96,
                    "line": {"color": "rgba(255,255,255,0.95)", "width": 1.15},
                    "showscale": False,
                },
                selectedpoints=focus_selected_points or None,
                selected={"marker": {"opacity": 1.0, "size": max(focus_sizes or [11]) + 4, "color": "#0f766e"}},
                unselected={"marker": {"opacity": 0.78 if focus_mode in {"inspect", "compare"} else 0.64}},
                hovertemplate=(
                    "<b>%{hovertext}</b><br>"
                    "Best places to start: %{customdata[2]:.1f}/10<br>"
                    "WSIS score: %{customdata[3]:.1f}/10<br>"
                    "Standout: %{customdata[4]}"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    if not labeled_frame.empty:
        figure.add_trace(
            go.Scattergeo(
                lat=labeled_frame["latitude"],
                lon=labeled_frame["longitude"],
                text=labeled_frame["label"],
                mode="text",
                textposition="top center",
                textfont={
                    "size": 10 if focus_mode in {"inspect", "compare"} else 9,
                    "color": "#1f2b28",
                },
                hoverinfo="skip",
                showlegend=False,
            )
        )

    figure.add_annotation(
        x=0.014,
        y=0.03,
        xref="paper",
        yref="paper",
        text="Glimmers hint at city potential. Bigger signals appear as you inspect more closely.",
        showarrow=False,
        font={"size": 11, "color": "#5b666a"},
        align="left",
        bgcolor="rgba(255,255,255,0.72)",
        bordercolor="rgba(91,102,106,0.12)",
        borderpad=6,
    )

    figure.update_layout(
        height=610 if focus_mode == "national" else 640,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        clickmode="event+select",
        font={"color": "#17212b", "family": "Plus Jakarta Sans, Arial, sans-serif"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        template="plotly_white",
    )
    figure.update_geos(
        scope="usa",
        projection_type="albers usa",
        center={"lat": float(focus["lat"]), "lon": float(focus["lon"])},
        projection_scale=float(focus["scale"]),
        showland=True,
        landcolor="rgb(247, 248, 246)",
        showcountries=False,
        showcoastlines=False,
        showlakes=False,
        showsubunits=True,
        subunitcolor="rgba(255,255,255,0.72)",
        subunitwidth=0.7,
        bgcolor="rgba(0,0,0,0)",
    )
    return figure


def render_map_state_bar(detail: CityDetail | None, compare_details: list[CityDetail], visible_count: int) -> None:
    with st.container(border=True):
        columns = st.columns([1.7, 1.1, 1.1])
        stage_title, stage_body = interaction_stage_copy(detail, compare_details)
        with columns[0]:
            st.write(stage_title)
            st.caption(stage_body)
        with columns[1]:
            chips = [f"{visible_count} visible", "Starter score"]
            if compare_details:
                chips.append(f"{len(compare_details)} compared")
            render_badges(chips)
        with columns[2]:
            if st.button("Clear selection", key="map_clear_selection", width="stretch", disabled=detail is None):
                clear_selected_city()
                st.rerun()
            if st.button("Reset discovery", key="map_reset_discovery", width="stretch"):
                reset_discovery_tray()
                st.rerun()


def render_filter_tray() -> None:
    with st.container(border=True):
        tray_columns = st.columns([1.1, 1.4, 0.9])
        with tray_columns[0]:
            st.selectbox("Region", ["All", "South", "West", "Midwest", "Northeast"], key="home_region")
        with tray_columns[1]:
            if st.session_state["home_selected_filters"]:
                render_badges(st.session_state["home_selected_filters"])
            else:
                st.caption("No quick filters")
        with tray_columns[2]:
            with st.popover("Adjust filters"):
                st.multiselect(
                    "Quick filters",
                    consumer_filter_labels(),
                    key="home_selected_filters",
                )
                st.caption("Human-readable filters first. Some civic and sector filters are heuristic placeholders for now.")
                first_row = st.columns(3)
                second_row = st.columns(2)
                slider_columns = [
                    (first_row[0], "affordability"),
                    (first_row[1], "job_market"),
                    (first_row[2], "safety"),
                    (second_row[0], "climate"),
                ]
                for column, weight_name in slider_columns:
                    with column:
                        st.slider(
                            WEIGHT_LABELS[weight_name],
                            min_value=0,
                            max_value=100,
                            step=5,
                            key=WEIGHT_STATE_KEYS[weight_name],
                            help=WEIGHT_HELP[weight_name],
                        )
                with second_row[1]:
                    st.caption("Social sentiment")
                    st.info("Shown as context only for the MVP. It does not change the ranked discovery score.")
        if st.session_state["home_selected_filters"]:
            st.caption(" | ".join(active_filter_descriptions(st.session_state["home_selected_filters"])))


def render_side_panel_intro(weights: ScoreWeights, visible_count: int, total_count: int) -> None:
    st.markdown("### Explore")
    st.html('<div class="wsis-side-note">Click a city for the short read. Use Decision when you need a yes/no verdict.</div>')
    render_badges([f"{visible_count} visible", f"{total_count} tracked"])
    st.caption(ranking_explanation(weights))


def render_selected_compare_links(compare_details: list[CityDetail]) -> None:
    if not compare_details:
        return
    st.caption("Selected for compare")
    render_badges([f"{detail.summary.name}, {detail.summary.state_code}" for detail in compare_details])


def render_side_panel(detail: CityDetail | None, weights: ScoreWeights, compare_details: list[CityDetail], available_slugs: set[str]) -> None:
    with st.container(border=True):
        if detail is None:
            render_side_panel_intro(weights, len(available_slugs), len(available_slugs))
            return

        st.html(
            f"""
            <div class="wsis-selected-callout">
              <div class="wsis-eyebrow">Now Inspecting</div>
              <h3 style="margin:0.2rem 0 0 0;">{html.escape(detail.summary.name)}, {html.escape(detail.summary.state_code)}</h3>
            </div>
            """,
        )
        render_badges(badge_labels(detail))
        score_columns = st.columns(2)
        score_columns[0].metric("WSIS score", detail.summary.overall_score)
        score_columns[1].metric("Start score", f"{best_places_to_start_score(detail, weights):.1f}")
        st.caption(detail.summary.score_context.explanation)
        if detail.summary.score_context.beta_warning:
            st.warning(detail.summary.score_context.beta_warning)
        st.caption("Core freshness: " + " | ".join(city_core_freshness_summary(detail)))
        st.caption(
            "Context freshness: "
            f"home price {freshness_badge(detail.metrics.median_home_price_source_date)} | "
            f"job growth {freshness_badge(detail.metrics.job_growth_source_date)}"
        )
        stat_columns = st.columns(2)
        for column, (label, value) in zip(stat_columns * 2, quick_stats(detail)):
            column.metric(label, value)

        action_columns = st.columns(2)
        with action_columns[0]:
            if st.button("View City Profile", key=f"panel_profile_{detail.summary.slug}", width="stretch"):
                open_profile(detail.summary.slug)
        with action_columns[1]:
            compare_label = (
                "Remove from Compare" if detail.summary.slug in current_compare_selection(available_slugs) else "Add to Compare"
            )
            if st.button(compare_label, key=f"panel_compare_{detail.summary.slug}", width="stretch"):
                toggle_compare_city(detail.summary.slug, available_slugs)
                st.rerun()
        action_footer = st.columns(2)
        with action_footer[0]:
            if st.button("Clear Inspection", key=f"panel_clear_{detail.summary.slug}", width="stretch"):
                clear_selected_city()
                st.rerun()
        with action_footer[1]:
            if st.button("Save coming soon", key=f"panel_save_{detail.summary.slug}", width="stretch", disabled=True):
                pass

        tabs = st.tabs(["Overview", "Social"])
        with tabs[0]:
            st.write(detail.summary.headline)
            st.caption(city_reason_snippet(detail, weights))
            st.caption(
                "Included in score: "
                + ", ".join(detail.summary.score_context.included_dimensions)
                + ". Context only: "
                + ", ".join(detail.summary.score_context.excluded_dimensions)
                + "."
            )
            if not compare_details:
                st.caption("Inspect here first, then add this city to compare only if it still feels like a live option.")
            elif detail.summary.slug not in {item.summary.slug for item in compare_details}:
                st.caption("Your compare tray is active. Keep inspecting here, then add this city only if it beats one of the current candidates.")
            else:
                st.caption("This city is already locked into compare. Inspect it here, then open the full comparison when you are ready.")
            for highlight in detail.highlights[:3]:
                st.write(f"- {highlight}")
        with tabs[1]:
            st.metric("Sentiment score", detail.reddit_panel.sentiment_score)
            render_badges(social_themes(detail))
            st.caption("Social context is not part of the ranked discovery score in the MVP.")
            st.write(detail.reddit_panel.summary)
            st.markdown(f"**{social_preview_title(detail)}**")
            st.write(social_excerpt(detail))

        render_selected_compare_links(compare_details)
        if len(compare_details) >= 2 and st.button("Launch Comparison", width="stretch"):
            open_comparison()


def render_compare_tray(compare_details: list[CityDetail], weights: ScoreWeights, available_slugs: set[str]) -> None:
    if len(compare_details) < 2:
        return
    with st.container(border=True):
        st.markdown("### Compare tray")
        st.caption("Decision support for two to three cities while the side panel keeps the active city in focus.")
        top_actions = st.columns([1, 1])
        with top_actions[0]:
            if st.button("Open full comparison", key="tray_open_comparison", width="stretch"):
                open_comparison()
        with top_actions[1]:
            if st.button("Clear compare tray", key="tray_clear_compare", width="stretch"):
                clear_compare_selection()
                st.rerun()

        compare_columns = st.columns(len(compare_details))
        active_slug = st.session_state.get("selected_city_slug", "")
        for column, detail in zip(compare_columns, compare_details):
            with column:
                with st.container(border=True):
                    st.caption("Comparison candidate")
                    st.markdown(f"### {detail.summary.name}, {detail.summary.state_code}")
                    status_labels = []
                    if detail.summary.slug == active_slug:
                        status_labels.append("Active inspection")
                    status_labels.extend(badge_labels(detail)[:2])
                    render_badges(status_labels)
                    metric_columns = st.columns(2)
                    metric_columns[0].metric("WSIS", detail.summary.overall_score)
                    metric_columns[1].metric("Start", f"{best_places_to_start_score(detail, weights):.1f}")
                    for label, value in quick_stats(detail)[:3]:
                        st.caption(f"{label}: {value}")
                    st.caption(city_reason_snippet(detail, weights))
                    action_columns = st.columns(2)
                    with action_columns[0]:
                        if st.button("Inspect", key=f"tray_inspect_{detail.summary.slug}", width="stretch"):
                            update_selected_city(detail.summary.slug)
                            st.rerun()
                    with action_columns[1]:
                        if st.button("Remove", key=f"tray_remove_{detail.summary.slug}", width="stretch"):
                            toggle_compare_city(detail.summary.slug, available_slugs)
                            st.rerun()

        compare_frame = pd.DataFrame(comparison_preview_rows(compare_details))
        st.dataframe(compare_frame, width="stretch", hide_index=True)
        st.caption(ranking_explanation(weights))


def render_top_match_card(detail: CityDetail, rank: int, available_slugs: set[str]) -> None:
    compare_slugs = current_compare_selection(available_slugs)
    compare_label = "Remove from Compare" if detail.summary.slug in compare_slugs else "Compare"
    is_selected = st.session_state.get("selected_city_slug", "") == detail.summary.slug
    status_labels = []
    if is_selected:
        status_labels.append("Active")
    if detail.summary.slug in compare_slugs:
        status_labels.append("Comparing")
    badges = status_labels + badge_labels(detail)[:2]
    stats = [
        ("WSIS", f"{detail.summary.overall_score:.1f}"),
        ("Start", f"{best_places_to_start_score(detail, current_weights()):.1f}"),
        ("Rent", f"${detail.metrics.median_rent:,.0f}"),
    ]
    badge_html = "".join(f'<span class="wsis-chip">{html.escape(label)}</span>' for label in badges)
    st.html(
        f"""
        <div class="wsis-compact-card">
          <div class="wsis-card-rank">Top match #{rank}</div>
          <div class="wsis-card-title">{html.escape(detail.summary.name)}, {html.escape(detail.summary.state_code)}</div>
          <div class="wsis-chip-row">{badge_html}</div>
          {compact_stats_html(stats)}
          <div class="wsis-card-copy">{html.escape(detail.summary.headline)}</div>
          <div class="wsis-muted-copy">{html.escape(city_reason_snippet(detail, current_weights()))}</div>
        </div>
        """,
    )

    action_columns = st.columns(2)
    with action_columns[0]:
        inspect_label = "Inspecting" if is_selected else "Inspect"
        if st.button(inspect_label, key=f"card_detail_{detail.summary.slug}", width="stretch", disabled=is_selected):
            update_selected_city(detail.summary.slug)
            st.rerun()
    with action_columns[1]:
        if st.button("Profile", key=f"card_profile_{detail.summary.slug}", width="stretch"):
            open_profile(detail.summary.slug)
    if st.button(compare_label, key=f"card_compare_{detail.summary.slug}", width="stretch"):
        toggle_compare_city(detail.summary.slug, available_slugs)
        st.rerun()


inject_styles()
initialize_state()

client = get_client()
weights = current_weights()
city_summaries, source = client.list_cities(weights)
all_details, _ = fetch_city_details(client, [city.slug for city in city_summaries], weights)

filtered_details = apply_consumer_filters(
    all_details,
    st.session_state["home_region"],
    st.session_state["home_selected_filters"],
)

if not filtered_details:
    st.html(
        """
        <div class="wsis-hero">
          <div class="wsis-eyebrow">Where Should I Start</div>
          <h1>No cities match the current tray setup.</h1>
          <p>Loosen a quick filter or switch the region in the filter tray to bring the discovery map back into view.</p>
        </div>
        """,
    )
    render_filter_tray()
    st.stop()

available_slugs = {detail.summary.slug for detail in filtered_details}
selected_city_slug = st.session_state.get("selected_city_slug", "")
if selected_city_slug not in available_slugs:
    selected_city_slug = ""
    st.session_state["selected_city_slug"] = ""

selected_detail = next(
    (detail for detail in filtered_details if detail.summary.slug == selected_city_slug),
    None,
)

compare_slugs = current_compare_selection(available_slugs)
compare_details = [detail for detail in filtered_details if detail.summary.slug in compare_slugs]
top_detail = filtered_details[0]
score_average = round(sum(detail.summary.overall_score for detail in filtered_details) / len(filtered_details), 2)

st.html(
    f"""
    <div class="wsis-hero">
      <div class="wsis-eyebrow">Where Should I Start</div>
      <h1>Explore where you could move before you commit to the wrong city.</h1>
      <p>Browse the market, inspect one city at a time, and narrow to a few realistic options before deeper research.</p>
      <div class="wsis-chip-row">
        <span class="wsis-chip">{len(filtered_details)} cities in play</span>
        <span class="wsis-chip">Top score: {top_detail.summary.name}, {top_detail.summary.state_code}</span>
        <span class="wsis-chip">Average fit: {score_average}</span>
      </div>
      <div class="wsis-note">Trust-first MVP: ranking uses source-backed affordability, jobs, safety, and climate. Social sentiment stays visible as context only.</div>
    </div>
    """,
)

st.html(
    """
    <div class="wsis-decision-cta">
      <div>
        <strong>Need a verdict instead of browsing?</strong>
        <span>Use the Decision workspace for offer salary, rent ceiling, and Sarah's evidence checks.</span>
      </div>
    </div>
    """,
)
st.page_link("pages/0_Decision.py", label="Open Decision workspace")

render_section_header(
    "Discovery Map",
    "Explore first",
    "Start with the map, not the dashboard. Hover for a quick signal, click a city to inspect it, and only move deeper when something looks worth your attention.",
)

main_columns = st.columns([2.7, 1], gap="large")
with main_columns[0]:
    with st.container(border=True):
        render_map_state_bar(selected_detail, compare_details, len(filtered_details))
        render_filter_tray()
        map_event = st.plotly_chart(
            build_map(
                filtered_details,
                weights,
                st.session_state["home_region"],
                selected_detail,
                compare_details,
            ),
            width="stretch",
            key="home_map_chart",
            on_select="rerun",
            selection_mode=("points",),
        )
        if map_event and map_event.selection.points:
            point = map_event.selection.points[0]
            custom_data = point.get("customdata")
            if custom_data:
                clicked_slug = custom_data[0]
                if clicked_slug in available_slugs and clicked_slug != st.session_state["selected_city_slug"]:
                    update_selected_city(clicked_slug)
                    st.rerun()
        st.caption("State fill uses the trust-first starter score. County lines add context. Click a city point to inspect it and use Clear selection to return to pure discovery mode.")
        render_compare_tray(compare_details, weights, available_slugs)
with main_columns[1]:
    render_side_panel(selected_detail, weights, compare_details, available_slugs)

render_section_header(
    "Top Matches",
    "Shortlist",
    "Three candidates, enough signal to choose what deserves inspection.",
)
top_cards = st.columns(min(3, len(filtered_details)))
for index, detail in enumerate(filtered_details[:3]):
    with top_cards[index]:
        render_top_match_card(detail, index + 1, available_slugs)

with st.expander("Why these cities surfaced"):
    focus_detail = selected_detail or top_detail
    strongest = strongest_dimensions(focus_detail.summary)[:3]
    st.write(ranking_explanation(weights))
    st.caption(
        f"{focus_detail.summary.name} is strongest on "
        + ", ".join(label.lower() for label, _ in strongest)
        + "."
    )
    reason_columns = st.columns(min(3, len(filtered_details)))
    for index, detail in enumerate(filtered_details[:3]):
        with reason_columns[index]:
            st.markdown(f"**{detail.summary.name}, {detail.summary.state_code}**")
            render_badges(badge_labels(detail))
            st.caption(city_reason_snippet(detail, weights))

with st.expander("Social context"):
    social_columns = st.columns(min(3, len(filtered_details)))
    for index, detail in enumerate(filtered_details[:3]):
        with social_columns[index]:
            stats = [
                ("Sentiment", f"{detail.reddit_panel.sentiment_score:.1f}"),
                ("Posts", str(detail.reddit_panel.posts_analyzed)),
                ("Days", str(detail.reddit_panel.lookback_days)),
            ]
            st.html(
                f"""
                <div class="wsis-compact-card">
                  <div class="wsis-card-title">{html.escape(detail.summary.name)}, {html.escape(detail.summary.state_code)}</div>
                  {compact_stats_html(stats)}
                  <div class="wsis-chip-row">{"".join(f'<span class="wsis-chip">{html.escape(label)}</span>' for label in social_themes(detail))}</div>
                  <div class="wsis-card-copy">{html.escape(detail.reddit_panel.summary)}</div>
                  <div class="wsis-muted-copy">Context only. Social sentiment does not change the rank.</div>
                </div>
                """,
            )
