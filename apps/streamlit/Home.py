from __future__ import annotations

import html

import pandas as pd
import plotly.express as px
import streamlit as st

from wsis.core.config import get_settings
from wsis.core.weights import WEIGHT_STATE_KEYS, default_score_weights, score_weights_from_state
from wsis.domain.models import CityDetail, CitySummary, ScoreWeights
from wsis.services.api_client import ApiCityClient
from wsis.ui.homepage import (
    badge_labels,
    city_reason_snippet,
    comparison_preview_rows,
    ranking_explanation,
    social_excerpt,
    social_preview_title,
    social_themes,
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
            padding: 1.5rem 1.6rem;
            margin-bottom: 0.4rem;
        }
        .wsis-hero h1 {
            font-size: 2.55rem;
            line-height: 1.05;
            margin: 0.25rem 0 0.8rem 0;
            color: #1f2b28;
        }
        .wsis-hero p {
            font-size: 1rem;
            color: #31403c;
            margin-bottom: 0.4rem;
        }
        .wsis-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin: 0.45rem 0 0.1rem 0;
        }
        .wsis-chip {
            display: inline-block;
            padding: 0.28rem 0.65rem;
            border-radius: 999px;
            background: #f3f0ea;
            border: 1px solid rgba(70, 66, 57, 0.12);
            color: #3a3d38;
            font-size: 0.82rem;
            font-weight: 600;
        }
        .wsis-note {
            border-left: 3px solid #b98652;
            padding-left: 0.8rem;
            margin-top: 0.7rem;
            color: #4b514b;
        }
        .wsis-placeholder {
            border: 1px dashed rgba(84, 96, 97, 0.35);
            border-radius: 18px;
            padding: 1rem;
            background: rgba(244, 241, 235, 0.6);
            min-height: 165px;
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
            padding-top: 0.25rem;
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
    st.session_state.setdefault("selected_city_slug", "")


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


def build_weights_section() -> ScoreWeights:
    render_section_header(
        "Score controls",
        "Tune your fit",
        "Set what matters most. WSIS normalizes these weights before scoring, so you can treat them as a preference mix rather than fixed math.",
    )
    with st.container(border=True):
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

        weights = current_weights()
        ordered_weights = sorted(
            weights.normalized().model_dump().items(),
            key=lambda item: item[1],
            reverse=True,
        )
        summary_columns = st.columns(3)
        summary_columns[0].metric("Lead priority", WEIGHT_LABELS[ordered_weights[0][0]])
        summary_columns[1].metric("Second priority", WEIGHT_LABELS[ordered_weights[1][0]])
        summary_columns[2].metric(
            "Current mix",
            " / ".join(
                f"{WEIGHT_LABELS[name]} {int(round(value * 100))}%"
                for name, value in ordered_weights[:3]
            ),
        )
        st.write(ranking_explanation(weights))
        return weights


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
        figure = px.scatter_mapbox(
            frame,
            lat="latitude",
            lon="longitude",
            color="score",
            size="score",
            hover_name="city",
            hover_data={"state": True, "headline": True, "latitude": False, "longitude": False},
            color_continuous_scale="YlGnBu",
            zoom=2.9,
            height=560,
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
            hover_data={"state": True, "headline": True},
            color_continuous_scale="YlGnBu",
            scope="usa",
            projection="albers usa",
            height=560,
        )

    figure.update_layout(
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        coloraxis_colorbar={"title": "WSIS score"},
    )
    figure.update_traces(marker={"opacity": 0.88, "line": {"color": "white", "width": 1}})
    return figure


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


def sync_compare_selection(filtered_cities: list[CitySummary]) -> list[str]:
    available_slugs = [city.slug for city in filtered_cities]
    selected = [slug for slug in st.session_state["home_compare_slugs"] if slug in available_slugs]
    target_default = min(2, len(available_slugs))
    for slug in available_slugs:
        if len(selected) >= target_default:
            break
        if slug not in selected:
            selected.append(slug)
    st.session_state["home_compare_slugs"] = selected[:3]
    return st.session_state["home_compare_slugs"]


def toggle_compare_city(slug: str, filtered_cities: list[CitySummary]) -> None:
    available_slugs = {city.slug for city in filtered_cities}
    selected = [item for item in st.session_state["home_compare_slugs"] if item in available_slugs]
    if slug in selected:
        selected.remove(slug)
    elif len(selected) < 3:
        selected.append(slug)
    else:
        st.session_state["home_compare_notice"] = "Comparison is limited to three cities on Home."
    st.session_state["home_compare_slugs"] = selected


def render_top_match_card(detail: CityDetail, rank: int, filtered_cities: list[CitySummary]) -> None:
    compare_slugs = st.session_state["home_compare_slugs"]
    compare_label = "Remove from compare" if detail.summary.slug in compare_slugs else "Compare"

    with st.container(border=True):
        st.caption(f"Top match #{rank}")
        st.markdown(f"### {detail.summary.name}, {detail.summary.state_code}")
        render_badges(badge_labels(detail))
        st.write(detail.summary.headline)
        metric_columns = st.columns(3)
        metric_columns[0].metric("Overall", detail.summary.overall_score)
        metric_columns[1].metric("Rent", f"${detail.metrics.median_rent:,.0f}")
        metric_columns[2].metric("Sentiment", detail.reddit_panel.sentiment_score)
        st.caption(city_reason_snippet(detail, current_weights()))

        action_columns = st.columns(2)
        with action_columns[0]:
            if st.button("View details", key=f"view_{detail.summary.slug}", use_container_width=True):
                open_profile(detail.summary.slug)
        with action_columns[1]:
            if st.button(compare_label, key=f"compare_{detail.summary.slug}", use_container_width=True):
                toggle_compare_city(detail.summary.slug, filtered_cities)
                st.rerun()


inject_styles()
initialize_state()

client = get_client()
weights = current_weights()
cities, source = client.list_cities(weights)

regions = ["All"] + sorted({city.region for city in cities})
if st.session_state["home_region"] not in regions:
    st.session_state["home_region"] = "All"
selected_region = st.session_state["home_region"]
filtered_cities = [
    city for city in cities if selected_region == "All" or city.region == selected_region
]

if not filtered_cities:
    st.warning("No cities match the active region filter. Reset the filter to continue.")
    st.stop()

compare_slugs = sync_compare_selection(filtered_cities)
top_city = filtered_cities[0]
score_average = round(sum(city.overall_score for city in filtered_cities) / len(filtered_cities), 2)
featured_slugs = [city.slug for city in filtered_cities[:3]]
featured_details, _ = fetch_city_details(client, featured_slugs, weights)

selected_city_slug = st.session_state.get("selected_city_slug") or top_city.slug
if selected_city_slug not in {city.slug for city in filtered_cities}:
    selected_city_slug = top_city.slug
    st.session_state["selected_city_slug"] = selected_city_slug
selected_detail, _ = client.get_city(selected_city_slug, weights)

st.markdown(
    f"""
    <div class="wsis-hero">
      <div class="wsis-eyebrow">Where Should I Start</div>
      <h1>Find the city that fits your twenties before you commit to a move.</h1>
      <p>WSIS is a map-first relocation discovery tool for early-career movers. Adjust your priorities, scan the shortlist, compare a few cities in place, and check the social reality before you talk yourself into the wrong move.</p>
      <div class="wsis-chip-row">
        <span class="wsis-chip">Current source: {html.escape(source)}</span>
        <span class="wsis-chip">{len(filtered_cities)} cities in view</span>
        <span class="wsis-chip">Top match: {html.escape(top_city.name)}, {html.escape(top_city.state_code)}</span>
        <span class="wsis-chip">Average score: {score_average}</span>
      </div>
      <div class="wsis-note">WSIS is now designed to support three actions from Home: browse the market, understand why a city is surfacing, and compare likely options before you leave the page.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

hero_metrics = st.columns(4)
hero_metrics[0].metric("Mapped cities", len(filtered_cities))
hero_metrics[1].metric("Top right now", f"{top_city.name}, {top_city.state_code}")
hero_metrics[2].metric("Average fit", score_average)
hero_metrics[3].metric("Cities in compare", len(compare_slugs))

weights = build_weights_section()

render_section_header(
    "Map discovery",
    "Browse the market",
    "Keep the current point-based map, but use it like a discovery canvas: filter the cohort, scan the score spread, and move straight into shortlist and comparison decisions.",
)
map_columns = st.columns([3, 1.3])
with map_columns[0]:
    st.plotly_chart(build_map(filtered_cities), use_container_width=True)
    st.caption(
        "Current map uses city points and the active WSIS score. Polygon geography and choropleths remain deferred to a later milestone."
    )
with map_columns[1]:
    with st.container(border=True):
        st.markdown("### Discovery filters")
        st.selectbox("Region", regions, key="home_region")
        st.metric("Cities in view", len(filtered_cities))
        st.metric("Top city in view", f"{top_city.name}, {top_city.state_code}")
        st.metric("Average score", score_average)
        st.caption(top_city.headline)
    with st.container(border=True):
        st.markdown("### Fast read")
        st.write(ranking_explanation(weights))
        st.caption(
            "Cities on this page are scored relative to the current tracked cohort, so use the ranking as a comparative filter rather than a national promise."
        )

render_section_header(
    "Top matches",
    "Shortlist",
    "The shortlist is now card-first. It should help a first-time user decide which cities deserve a closer look before they ever open the full profile page.",
)
top_cards = st.columns(len(featured_details)) if featured_details else []
for index, detail in enumerate(featured_details):
    with top_cards[index]:
        render_top_match_card(detail, index + 1, filtered_cities)

with st.container(border=True):
    st.markdown("### More cities to inspect")
    explorer_columns = st.columns([1.3, 1])
    with explorer_columns[0]:
        selected_city_slug = st.selectbox(
            "Focus city",
            [city.slug for city in filtered_cities],
            index=next(
                index for index, city in enumerate(filtered_cities) if city.slug == selected_city_slug
            ),
            format_func=lambda slug: next(
                f"{city.name}, {city.state_code}" for city in filtered_cities if city.slug == slug
            ),
        )
        st.session_state["selected_city_slug"] = selected_city_slug
        selected_detail, _ = client.get_city(selected_city_slug, weights)
        render_badges(badge_labels(selected_detail))
        st.caption(city_reason_snippet(selected_detail, weights))
    with explorer_columns[1]:
        st.metric("Focus city score", selected_detail.summary.overall_score)
        st.metric("Focus city rent", f"${selected_detail.metrics.median_rent:,.0f}")
        if st.button("View full city profile", type="primary", use_container_width=True):
            open_profile(selected_detail.summary.slug)

with st.expander("See full score table", expanded=False):
    shortlist_frame = pd.DataFrame(
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
    st.dataframe(shortlist_frame, use_container_width=True, hide_index=True)

render_section_header(
    "Quick comparison",
    "Compare in place",
    "Use this strip to compare two or three realistic options without leaving Home. The dedicated comparison page still exists for deeper side-by-side work.",
)
with st.container(border=True):
    st.multiselect(
        "Cities to compare",
        [city.slug for city in filtered_cities],
        format_func=lambda slug: next(
            f"{city.name}, {city.state_code}" for city in filtered_cities if city.slug == slug
        ),
        key="home_compare_slugs",
        max_selections=3,
    )
    if st.session_state.get("home_compare_notice"):
        st.info(st.session_state.pop("home_compare_notice"))
    compare_slugs = sync_compare_selection(filtered_cities)
    if len(compare_slugs) >= 2:
        comparison_details, comparison_source = client.compare_cities(compare_slugs, weights)
        compare_frame = pd.DataFrame(comparison_preview_rows(comparison_details))
        st.caption(f"Comparison source: {comparison_source}.")
        st.dataframe(compare_frame, use_container_width=True, hide_index=True)
    else:
        placeholder_card(
            "Comparison strip waiting for two cities",
            "Add two or three cities from the shortlist cards or the selector above to see a compact rent, income, unemployment, sentiment, and overall-score comparison.",
            "The deeper radar and multi-city page remain available on the dedicated Comparison screen.",
        )

render_section_header(
    "Why these cities",
    "Read the ranking",
    "Translate the score into plain language so users can understand why cities are surfacing, not just stare at numbers.",
)
explanation_columns = st.columns([1.05, 1.2])
with explanation_columns[0]:
    with st.container(border=True):
        st.markdown("### Ranking logic in product language")
        st.write(ranking_explanation(weights))
        primary_dimensions = strongest_dimensions(selected_detail.summary)[:3]
        st.caption(
            f"{selected_detail.summary.name} currently performs best on "
            + ", ".join(label.lower() for label, _ in primary_dimensions[:-1])
            + (f", and {primary_dimensions[-1][0].lower()}" if len(primary_dimensions) > 1 else "")
            + "."
        )
        for label, score in primary_dimensions:
            st.markdown(f"**{label}**")
            st.progress(min(score / 10, 1.0))
            st.caption(f"{label} is scoring {score}/10 for {selected_detail.summary.name}.")
with explanation_columns[1]:
    with st.container(border=True):
        st.markdown("### Why the shortlist is surfacing")
        for detail in featured_details:
            st.markdown(f"**{detail.summary.name}, {detail.summary.state_code}**")
            st.write(city_reason_snippet(detail, weights))
            render_badges(badge_labels(detail))
            st.caption(detail.summary.headline)

render_section_header(
    "Social reality",
    "What it actually feels like",
    "A score is not enough. The home page should preview the social read in a way that feels deliberate, even when some cities only have thin structured data.",
)
social_cards = st.columns(3)
for index, column in enumerate(social_cards):
    with column:
        if index < len(featured_details):
            detail = featured_details[index]
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
    "Future watchlist",
    "Coming soon",
    "These placeholders mark the next consumer product surfaces without pretending the persistence layer already exists.",
)
watchlist_columns = st.columns(3)
with watchlist_columns[0]:
    placeholder_card(
        "Saved cities",
        "Build a personal shortlist and return to the same markets after you change priorities or narrow your move window.",
        "Placeholder for watchlist persistence and saved city actions.",
    )
with watchlist_columns[1]:
    placeholder_card(
        "Alerts and refreshes",
        "See when a city's ranking changes because unemployment, rent pressure, or social sentiment shifts enough to matter.",
        "Placeholder for refresh jobs and score-change monitoring.",
    )
with watchlist_columns[2]:
    placeholder_card(
        "Weight presets",
        "Save modes like budget-first, strong-jobs, or warm-weather reset so the home experience becomes reusable instead of one-off.",
        "Placeholder for saved preference profiles and onboarding flows.",
    )
