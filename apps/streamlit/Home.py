from __future__ import annotations

import html

import pandas as pd
import plotly.express as px
import streamlit as st

from wsis.core.config import get_settings
from wsis.core.weights import WEIGHT_STATE_KEYS, default_score_weights, score_weights_from_state
from wsis.domain.models import CityDetail, ScoreWeights
from wsis.services.api_client import ApiCityClient
from wsis.ui.homepage import (
    active_filter_descriptions,
    apply_consumer_filters,
    badge_labels,
    city_reason_snippet,
    comparison_preview_rows,
    consumer_filter_labels,
    filter_option_by_label,
    quick_stats,
    ranking_explanation,
    social_excerpt,
    social_preview_title,
    social_themes,
    standout_attribute,
    strongest_dimensions,
)


st.set_page_config(page_title="WSIS", layout="wide")


WEIGHT_LABELS = {
    "affordability": "Affordability",
    "job_market": "Job market",
    "safety": "Safety",
    "climate": "Climate",
    "social_sentiment": "Social sentiment",
}

WEIGHT_HELP = {
    "affordability": "Lower cost pressure relative to income and home-value proxy.",
    "job_market": "Career upside from proxy job growth and unemployment conditions.",
    "safety": "Relative safety based on the current source crime-rate slice.",
    "climate": "Comfort score based on temperature and sunny-day inputs.",
    "social_sentiment": "Current social signal drawn from the city sentiment input.",
}


@st.cache_resource
def get_client() -> ApiCityClient:
    return ApiCityClient()


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .wsis-eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-size: 0.78rem;
            color: #7f674f;
            font-weight: 700;
        }
        .wsis-hero {
            background: linear-gradient(135deg, #f4efe6 0%, #e6efe9 55%, #d8e6ea 100%);
            border: 1px solid rgba(104, 89, 70, 0.18);
            border-radius: 24px;
            padding: 1.2rem 1.3rem;
            margin-bottom: 0.65rem;
        }
        .wsis-hero h1 {
            font-size: 2.35rem;
            line-height: 1.02;
            margin: 0.2rem 0 0.55rem 0;
            color: #1f2b28;
        }
        .wsis-hero p {
            font-size: 0.98rem;
            color: #31403c;
            margin-bottom: 0.3rem;
        }
        .wsis-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin: 0.45rem 0 0.1rem 0;
        }
        .wsis-chip {
            display: inline-block;
            padding: 0.26rem 0.62rem;
            border-radius: 999px;
            background: #f3f0ea;
            border: 1px solid rgba(70, 66, 57, 0.12);
            color: #3a3d38;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .wsis-note {
            border-left: 3px solid #b98652;
            padding-left: 0.75rem;
            margin-top: 0.55rem;
            color: #4b514b;
        }
        .wsis-placeholder {
            border: 1px dashed rgba(84, 96, 97, 0.35);
            border-radius: 18px;
            padding: 1rem;
            background: rgba(244, 241, 235, 0.6);
            min-height: 150px;
        }
        .wsis-placeholder h4 {
            margin: 0 0 0.45rem 0;
            color: #23302c;
        }
        .wsis-placeholder p {
            color: #505953;
            margin-bottom: 0.65rem;
        }
        .wsis-mini {
            font-size: 0.86rem;
            color: #6b726d;
        }
        .wsis-section-space {
            padding-top: 0.15rem;
        }
        .wsis-map-shell {
            border: 1px solid rgba(90, 101, 100, 0.18);
            border-radius: 22px;
            background: linear-gradient(180deg, rgba(250,248,243,0.92) 0%, rgba(245,248,246,0.9) 100%);
            padding: 0.85rem;
        }
        .wsis-tray {
            border: 1px solid rgba(84, 96, 97, 0.2);
            border-radius: 18px;
            background: rgba(255,255,255,0.7);
            padding: 0.8rem;
        }
        .wsis-tray-compact {
            border: 1px solid rgba(84, 96, 97, 0.18);
            border-radius: 16px;
            background: rgba(248, 247, 242, 0.94);
            padding: 0.7rem 0.8rem;
            margin-top: 0.55rem;
        }
        .wsis-state-bar {
            border: 1px solid rgba(84, 96, 97, 0.14);
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.72);
            padding: 0.75rem 0.85rem;
            margin-bottom: 0.7rem;
        }
        .wsis-selected-callout {
            border: 1px solid rgba(185, 134, 82, 0.28);
            background: linear-gradient(135deg, rgba(249, 243, 232, 0.95) 0%, rgba(247, 250, 248, 0.9) 100%);
            border-radius: 16px;
            padding: 0.8rem;
            margin-bottom: 0.8rem;
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
    st.markdown('<div class="wsis-section-space">', unsafe_allow_html=True)
    st.markdown(f'<div class="wsis-eyebrow">{html.escape(eyebrow)}</div>', unsafe_allow_html=True)
    st.subheader(title)
    st.caption(description)
    st.markdown("</div>", unsafe_allow_html=True)


def render_badges(labels: list[str]) -> None:
    if not labels:
        return
    chips = "".join(
        f'<span class="wsis-chip">{html.escape(label)}</span>' for label in labels
    )
    st.markdown(f'<div class="wsis-chip-row">{chips}</div>', unsafe_allow_html=True)


def placeholder_card(title: str, body: str, footer: str) -> None:
    st.markdown(
        f"""
        <div class="wsis-placeholder">
          <h4>{html.escape(title)}</h4>
          <p>{html.escape(body)}</p>
          <div class="wsis-mini">{html.escape(footer)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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


def clear_compare_selection() -> None:
    st.session_state["home_compare_slugs"] = []


def build_map(details: list[CityDetail], selected_slug: str | None):
    settings = get_settings()
    frame = pd.DataFrame(
        [
            {
                "slug": detail.summary.slug,
                "city": detail.summary.name,
                "state": detail.summary.state,
                "score": detail.summary.overall_score,
                "latitude": detail.summary.latitude,
                "longitude": detail.summary.longitude,
                "standout": standout_attribute(detail),
            }
            for detail in details
        ]
    )

    if settings.mapbox_token:
        px.set_mapbox_access_token(settings.mapbox_token)
        figure = px.scatter_mapbox(
            frame,
            lat="latitude",
            lon="longitude",
            color="score",
            size="score",
            hover_name="city",
            hover_data={
                "state": True,
                "score": True,
                "standout": True,
                "latitude": False,
                "longitude": False,
            },
            custom_data=["slug"],
            color_continuous_scale="YlGnBu",
            zoom=2.9,
            height=620,
            mapbox_style="carto-positron",
        )
    else:
        figure = px.scatter_geo(
            frame,
            lat="latitude",
            lon="longitude",
            color="score",
            size="score",
            hover_name="city",
            hover_data={
                "state": True,
                "score": True,
                "standout": True,
            },
            custom_data=["slug"],
            color_continuous_scale="YlGnBu",
            scope="usa",
            projection="albers usa",
            height=620,
        )

    selected_points = frame.index[frame["slug"] == selected_slug].tolist() if selected_slug else []
    figure.update_layout(
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        coloraxis_colorbar={"title": "WSIS score"},
        clickmode="event+select",
    )
    figure.update_traces(
        marker={"opacity": 0.88, "line": {"color": "white", "width": 1.2}},
        selectedpoints=selected_points or None,
        selected={"marker": {"opacity": 1.0, "size": 24, "color": "#0f766e"}},
        unselected={"marker": {"opacity": 0.42}},
    )
    return figure


def render_map_state_bar(detail: CityDetail | None, compare_details: list[CityDetail], visible_count: int) -> None:
    st.markdown('<div class="wsis-state-bar">', unsafe_allow_html=True)
    columns = st.columns([1.5, 1.2, 0.8, 0.8])
    with columns[0]:
        st.caption("Inspection state")
        if detail is None:
            st.write("Discovery mode")
            st.caption("Click a city to inspect it in the side panel.")
        else:
            st.write(f"Inspecting {detail.summary.name}, {detail.summary.state_code}")
            st.caption("This city is highlighted on the map and expanded in the side panel.")
    with columns[1]:
        st.caption("In play")
        chips = [f"{visible_count} cities visible"]
        if compare_details:
            chips.append(f"{len(compare_details)} in compare tray")
        render_badges(chips)
    with columns[2]:
        st.caption("Selection")
        if st.button("Clear selection", key="map_clear_selection", width="stretch", disabled=detail is None):
            clear_selected_city()
            st.rerun()
    with columns[3]:
        st.caption("Reset")
        if st.button("Reset discovery", key="map_reset_discovery", width="stretch"):
            reset_discovery_tray()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_filter_tray() -> None:
    st.markdown('<div class="wsis-tray-compact">', unsafe_allow_html=True)
    tray_columns = st.columns([1.2, 1.4, 0.9])
    with tray_columns[0]:
        st.caption("Filter tray")
        st.selectbox("Region", ["All", "South", "West", "Midwest", "Northeast"], key="home_region")
    with tray_columns[1]:
        st.caption("Active quick filters")
        if st.session_state["home_selected_filters"]:
            render_badges(st.session_state["home_selected_filters"])
        else:
            st.caption("No quick filters active yet.")
    with tray_columns[2]:
        st.caption("Controls")
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
                (second_row[1], "social_sentiment"),
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
    if st.session_state["home_selected_filters"]:
        st.caption(" | ".join(active_filter_descriptions(st.session_state["home_selected_filters"])))
    st.markdown("</div>", unsafe_allow_html=True)


def render_side_panel_intro(weights: ScoreWeights, visible_count: int, total_count: int) -> None:
    st.markdown("### Explore the map")
    st.caption("Hover for a quick read. Click a city to turn this panel into an inspection view.")
    render_badges([f"{visible_count} visible", f"{total_count} tracked"])
    st.write("Use the filter tray only when you want to steer the map. Use compare only when two or three options start to feel real.")
    st.caption(ranking_explanation(weights))
    st.info("Inspection tabs and deep-dive actions appear here after selection.")


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

        st.markdown(
            f"""
            <div class="wsis-selected-callout">
              <div class="wsis-eyebrow">Now Inspecting</div>
              <h3 style="margin:0.2rem 0 0 0;">{html.escape(detail.summary.name)}, {html.escape(detail.summary.state_code)}</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_badges(badge_labels(detail))
        st.metric("WSIS score", detail.summary.overall_score)
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
            st.caption("Inspect here first, then either open the full profile or keep the city in compare.")
            for highlight in detail.highlights[:3]:
                st.write(f"- {highlight}")
        with tabs[1]:
            st.metric("Sentiment score", detail.reddit_panel.sentiment_score)
            render_badges(social_themes(detail))
            st.write(detail.reddit_panel.summary)
            st.markdown(f"**{social_preview_title(detail)}**")
            st.write(social_excerpt(detail))

        render_selected_compare_links(compare_details)
        if len(compare_details) >= 2 and st.button("Launch Comparison", width="stretch"):
            open_comparison()


def render_compare_tray(compare_details: list[CityDetail], weights: ScoreWeights, available_slugs: set[str]) -> None:
    if len(compare_details) < 2:
        return
    st.markdown('<div class="wsis-tray">', unsafe_allow_html=True)
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
                st.metric("Score", detail.summary.overall_score)
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
    st.markdown("</div>", unsafe_allow_html=True)


def render_top_match_card(detail: CityDetail, rank: int, available_slugs: set[str]) -> None:
    compare_slugs = current_compare_selection(available_slugs)
    compare_label = "Remove from Compare" if detail.summary.slug in compare_slugs else "Compare"
    is_selected = st.session_state.get("selected_city_slug", "") == detail.summary.slug

    with st.container(border=True):
        st.caption(f"Top match #{rank}")
        st.markdown(f"### {detail.summary.name}, {detail.summary.state_code}")
        status_labels = []
        if is_selected:
            status_labels.append("Active inspection")
        if detail.summary.slug in compare_slugs:
            status_labels.append("In compare tray")
        if status_labels:
            render_badges(status_labels)
        st.metric("Score", detail.summary.overall_score)
        render_badges(badge_labels(detail))
        st.write(detail.summary.headline)
        st.caption(city_reason_snippet(detail, current_weights()))
        st.caption("Inspect here first, then move deeper into the profile or compare tray.")

        action_columns = st.columns(3)
        with action_columns[0]:
            inspect_label = "Inspecting" if is_selected else "Inspect"
            if st.button(inspect_label, key=f"card_detail_{detail.summary.slug}", width="stretch", disabled=is_selected):
                update_selected_city(detail.summary.slug)
                st.rerun()
        with action_columns[1]:
            if st.button("Profile", key=f"card_profile_{detail.summary.slug}", width="stretch"):
                open_profile(detail.summary.slug)
        with action_columns[2]:
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
    st.markdown(
        """
        <div class="wsis-hero">
          <div class="wsis-eyebrow">Where Should I Start</div>
          <h1>No cities match the current tray setup.</h1>
          <p>Loosen a quick filter or switch the region in the filter tray to bring the discovery map back into view.</p>
        </div>
        """,
        unsafe_allow_html=True,
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

st.markdown(
    f"""
    <div class="wsis-hero">
      <div class="wsis-eyebrow">Where Should I Start</div>
      <h1>Explore where you could move before you commit to the wrong city.</h1>
      <p>Browse the market, inspect one city at a time, and only lock in comparison when a few options actually feel plausible.</p>
      <div class="wsis-chip-row">
        <span class="wsis-chip">Source: {html.escape(source)}</span>
        <span class="wsis-chip">{len(filtered_details)} cities in play</span>
        <span class="wsis-chip">Top score: {top_detail.summary.name}, {top_detail.summary.state_code}</span>
        <span class="wsis-chip">Average fit: {score_average}</span>
      </div>
      <div class="wsis-note">Map for discovery. Side panel for inspection. Trays for control and decision support.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

render_section_header(
    "Discovery Map",
    "Explore first",
    "Start with the map, not the dashboard. Hover for a quick signal, click a city to inspect it, and only move deeper when something looks worth your attention.",
)

main_columns = st.columns([2.7, 1], gap="large")
with main_columns[0]:
    st.markdown('<div class="wsis-map-shell">', unsafe_allow_html=True)
    render_map_state_bar(selected_detail, compare_details, len(filtered_details))
    render_filter_tray()
    map_event = st.plotly_chart(
        build_map(filtered_details, selected_city_slug or None),
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
            if clicked_slug != st.session_state["selected_city_slug"]:
                update_selected_city(clicked_slug)
                st.rerun()
    st.caption("Hover for a quick read. Click a point to inspect the city in the side panel. Use Clear selection to return to pure discovery mode.")
    render_compare_tray(compare_details, weights, available_slugs)
    st.markdown("</div>", unsafe_allow_html=True)
with main_columns[1]:
    render_side_panel(selected_detail, weights, compare_details, available_slugs)

render_section_header(
    "Top Matches",
    "Shortlist",
    "Shortlist cards help you move from broad exploration to a few plausible options without losing the map-first feel.",
)
top_cards = st.columns(min(3, len(filtered_details)))
for index, detail in enumerate(filtered_details[:3]):
    with top_cards[index]:
        render_top_match_card(detail, index + 1, available_slugs)

render_section_header(
    "Why These Cities",
    "Readable logic",
    "Translate the ranking model into product language so the shortlist feels understandable instead of opaque.",
)
reason_columns = st.columns([1.05, 1.2])
with reason_columns[0]:
    with st.container(border=True):
        st.markdown("### Why the ranking looks like this")
        st.write(ranking_explanation(weights))
        focus_detail = selected_detail or top_detail
        strongest = strongest_dimensions(focus_detail.summary)[:3]
        st.caption(f"{focus_detail.summary.name} currently leads on " + ", ".join(label.lower() for label, _ in strongest) + ".")
        for label, score in strongest:
            st.markdown(f"**{label}**")
            st.progress(min(score / 10, 1.0))
            st.caption(f"{label} is currently scoring {score}/10.")
with reason_columns[1]:
    with st.container(border=True):
        st.markdown("### City-level read")
        for detail in filtered_details[:3]:
            st.markdown(f"**{detail.summary.name}, {detail.summary.state_code}**")
            st.write(city_reason_snippet(detail, weights))
            render_badges(badge_labels(detail))
            st.caption(detail.summary.headline)

render_section_header(
    "Social Reality",
    "What it actually feels like",
    "Keep the social read lightweight but intentional: sentiment score, a couple of themes, and a short excerpt that feels more human than a pure metric.",
)
social_columns = st.columns(3)
for index, column in enumerate(social_columns):
    with column:
        if index < len(filtered_details[:3]):
            detail = filtered_details[index]
            with st.container(border=True):
                st.markdown(f"### {detail.summary.name}, {detail.summary.state_code}")
                st.metric("Sentiment", detail.reddit_panel.sentiment_score)
                render_badges(social_themes(detail))
                st.caption(
                    f"{detail.reddit_panel.posts_analyzed} posts analyzed | {detail.reddit_panel.lookback_days}-day lookback"
                )
                st.write(detail.reddit_panel.summary)
                st.markdown(f"**{social_preview_title(detail)}**")
                st.write(social_excerpt(detail))
        else:
            placeholder_card(
                "Social preview loading",
                "As richer city-level social summaries arrive, this area can expand into a fuller what-it's-like panel directly on Home.",
                "Current version intentionally stays lightweight and structured.",
            )

render_section_header(
    "Future Watchlist",
    "Coming soon",
    "These placeholders make the future product shape obvious without pretending persistence or auth already exist.",
)
watchlist_columns = st.columns(3)
with watchlist_columns[0]:
    placeholder_card(
        "Saved cities",
        "Build a personal shortlist and return to the same markets after your priorities change.",
        "Placeholder for watchlist persistence and saved city actions.",
    )
with watchlist_columns[1]:
    placeholder_card(
        "Alerts and refreshes",
        "Track when a city's score meaningfully changes because rent, unemployment, or social sentiment moves.",
        "Placeholder for refresh jobs and score-change monitoring.",
    )
with watchlist_columns[2]:
    placeholder_card(
        "Weight presets",
        "Save modes like budget-first or strong-jobs so discovery feels reusable instead of one-off.",
        "Placeholder for saved preference profiles and onboarding flows.",
    )
