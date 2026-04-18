from __future__ import annotations

import html

import pandas as pd
import plotly.express as px
import streamlit as st

from wsis.core.config import get_settings
from wsis.core.weights import WEIGHT_STATE_KEYS, default_score_weights, score_weights_from_state
from wsis.domain.models import CityDetail, CitySummary, ScoreWeights
from wsis.services.api_client import ApiCityClient


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


def current_weights() -> ScoreWeights:
    return score_weights_from_state(st.session_state)


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
        normalized = weights.normalized().model_dump()
        ordered_weights = sorted(normalized.items(), key=lambda item: item[1], reverse=True)
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
        st.caption(
            "Current shortlist reflects your active weight mix, region filter, and the current peer cohort. "
            "Use these controls to shift the ranking, then open a city profile for the full detail view."
        )
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


def city_badges(city: CitySummary) -> list[str]:
    badges: list[str] = []
    if city.overall_score >= 7.5:
        badges.append("High overall fit")
    breakdown = city.score_breakdown
    if breakdown.affordability >= 7:
        badges.append("Budget friendlier")
    if breakdown.job_market >= 7:
        badges.append("Career upside")
    if breakdown.safety >= 7:
        badges.append("Safer peer set")
    if breakdown.climate >= 7:
        badges.append("Climate comfort")
    if breakdown.social_sentiment >= 6.5:
        badges.append("Positive social signal")
    badges.append(city.region)
    deduped: list[str] = []
    for badge in badges:
        if badge not in deduped:
            deduped.append(badge)
    return deduped[:4]


def strongest_dimensions(city: CitySummary) -> list[tuple[str, float]]:
    return sorted(
        city.score_breakdown.as_dict().items(),
        key=lambda item: item[1],
        reverse=True,
    )


def overall_summary_note(city: CitySummary) -> str:
    top_dimensions = strongest_dimensions(city)[:2]
    top_labels = " and ".join(label.lower() for label, _ in top_dimensions)
    return f"{city.name} is surfacing because it currently scores best on {top_labels} within your active weighting mix."


def weight_focus_labels(weights: ScoreWeights) -> list[str]:
    ordered = sorted(
        weights.normalized().model_dump().items(),
        key=lambda item: item[1],
        reverse=True,
    )
    return [f"{WEIGHT_LABELS[name]} {int(round(value * 100))}%" for name, value in ordered[:3]]


def open_profile(slug: str) -> None:
    st.session_state["selected_city_slug"] = slug
    st.switch_page("pages/1_City_Profile.py")


def shortlist_frame(cities: list[CitySummary]) -> pd.DataFrame:
    return pd.DataFrame(
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
            for city in cities
        ]
    )


def render_city_card(city: CitySummary, rank: int) -> None:
    with st.container(border=True):
        st.caption(f"Top match #{rank}")
        st.markdown(f"### {city.name}, {city.state_code}")
        render_badges(city_badges(city))
        st.write(city.headline)
        card_metrics = st.columns(3)
        card_metrics[0].metric("WSIS score", city.overall_score)
        card_metrics[1].metric("Jobs", city.score_breakdown.job_market)
        card_metrics[2].metric("Social", city.score_breakdown.social_sentiment)
        st.caption(overall_summary_note(city))
        if st.button("Open city profile", key=f"card_{city.slug}", use_container_width=True):
            open_profile(city.slug)


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

top_city = filtered_cities[0]
score_average = round(sum(city.overall_score for city in filtered_cities) / len(filtered_cities), 2)

selected_city_slug = st.session_state.get("selected_city_slug", top_city.slug)
if selected_city_slug not in {city.slug for city in filtered_cities}:
    selected_city_slug = top_city.slug
    st.session_state["selected_city_slug"] = selected_city_slug
selected_city = next(city for city in filtered_cities if city.slug == selected_city_slug)
selected_detail, detail_source = client.get_city(selected_city_slug, weights)

st.markdown(
    f"""
    <div class="wsis-hero">
      <div class="wsis-eyebrow">Where Should I Start</div>
      <h1>Find the city that fits your twenties before you commit to a move.</h1>
      <p>WSIS is a map-first relocation discovery tool for early-career movers. Adjust your priorities, scan the shortlist, and check the social reality before you talk yourself into the wrong city.</p>
      <div class="wsis-chip-row">
        <span class="wsis-chip">Current source: {html.escape(source)}</span>
        <span class="wsis-chip">{len(filtered_cities)} cities in view</span>
        <span class="wsis-chip">Top match: {html.escape(top_city.name)}, {html.escape(top_city.state_code)}</span>
        <span class="wsis-chip">Average score: {score_average}</span>
      </div>
      <div class="wsis-note">This page is the consumer product skeleton: tune the scoring mix, browse the map, inspect the shortlist, then open a city profile when a place starts to feel real.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

hero_metrics = st.columns(4)
hero_metrics[0].metric("Mapped cities", len(filtered_cities))
hero_metrics[1].metric("Top right now", f"{top_city.name}, {top_city.state_code}")
hero_metrics[2].metric("Average fit", score_average)
hero_metrics[3].metric("Active priorities", ", ".join(weight_focus_labels(weights)[:2]))

weights = build_weights_section()

render_section_header(
    "Map discovery",
    "Browse the market",
    "Keep the current point-based map, but use it like a product discovery canvas: filter the cohort, scan the score spread, and identify where to dig deeper.",
)
map_columns = st.columns([3, 1.3])
with map_columns[0]:
    st.plotly_chart(build_map(filtered_cities), use_container_width=True)
    st.caption(
        "Current map uses city points and the active WSIS score. Polygon geography and choropleths are explicitly deferred to a later milestone."
    )
with map_columns[1]:
    with st.container(border=True):
        st.markdown("### Discovery filters")
        st.selectbox("Region", regions, key="home_region")
        st.metric("Cities in view", len(filtered_cities))
        st.metric("Top city in view", f"{top_city.name}, {top_city.state_code}")
        st.metric("Average score", score_average)
        render_badges(city_badges(top_city))
        st.caption(top_city.headline)
    with st.container(border=True):
        st.markdown("### What to do next")
        st.write("1. Adjust the weight mix above.")
        st.write("2. Scan where the score clusters on the map.")
        st.write("3. Use the shortlist below to pick a city for deeper review.")

render_section_header(
    "Top matches",
    "Shortlist",
    "A product-style shortlist should tell you what rose to the top before you commit to the full profile. These cards stay lightweight while preserving the current selection and navigation flow.",
)
top_cards = st.columns(3)
for index, city in enumerate(filtered_cities[:3]):
    with top_cards[index]:
        render_city_card(city, index + 1)

shortlist_columns = st.columns([1.5, 1])
with shortlist_columns[0]:
    with st.container(border=True):
        st.markdown("### Full shortlist table")
        st.dataframe(shortlist_frame(filtered_cities), use_container_width=True, hide_index=True)
with shortlist_columns[1]:
    with st.container(border=True):
        st.markdown("### Focus city")
        selected_city_slug = st.selectbox(
            "Open a city profile",
            [city.slug for city in filtered_cities],
            index=next(
                index for index, city in enumerate(filtered_cities) if city.slug == selected_city.slug
            ),
            format_func=lambda slug: next(
                f"{city.name}, {city.state_code}" for city in filtered_cities if city.slug == slug
            ),
        )
        st.session_state["selected_city_slug"] = selected_city_slug
        selected_city = next(city for city in filtered_cities if city.slug == selected_city_slug)
        selected_detail, detail_source = client.get_city(selected_city_slug, weights)
        render_badges(city_badges(selected_city))
        st.markdown(f"### {selected_city.name}, {selected_city.state_code}")
        st.write(selected_city.headline)
        focus_metrics = st.columns(2)
        focus_metrics[0].metric("WSIS score", selected_city.overall_score)
        focus_metrics[1].metric("Social", selected_city.score_breakdown.social_sentiment)
        if st.button("View full city profile", type="primary", use_container_width=True):
            open_profile(selected_city.slug)

render_section_header(
    "Why these cities",
    "Read the ranking",
    "This section explains the shortlist instead of just displaying it. The point is to make the ranking legible even before neighborhood lenses and deeper comparison tooling exist.",
)
explanation_columns = st.columns([1.2, 1])
with explanation_columns[0]:
    with st.container(border=True):
        st.markdown(f"### Why {selected_city.name} is showing up")
        st.write(overall_summary_note(selected_city))
        for label, score in strongest_dimensions(selected_city)[:3]:
            st.markdown(f"**{label}**")
            st.progress(min(score / 10, 1.0))
            st.caption(f"{label} is currently scoring {score}/10 for {selected_city.name}.")
with explanation_columns[1]:
    with st.container(border=True):
        st.markdown("### How to read the score")
        render_badges(weight_focus_labels(weights))
        st.write(
            "WSIS compares each city against the current cohort rather than a national baseline. "
            "That means the shortlist is best read as a relative fit ranking for this tool's tracked markets."
        )
        st.caption(
            "Current formula blends affordability, job market, safety, climate, and social sentiment. "
            "The detail page adds source-backed highlights and a stronger social reality read."
        )

render_section_header(
    "Social reality preview",
    "What it actually feels like",
    "The homepage should preview the consumer promise: not just a score, but a believable read on what living there might actually feel like.",
)
social_columns = st.columns([1.15, 1])
with social_columns[0]:
    with st.container(border=True):
        st.markdown(f"### {selected_city.name}, {selected_city.state_code}")
        st.caption(f"Preview source: {detail_source}")
        st.metric("Reddit sentiment", selected_detail.reddit_panel.sentiment_score)
        render_badges(
            [
                f"{selected_detail.reddit_panel.posts_analyzed} posts analyzed",
                f"{selected_detail.reddit_panel.lookback_days}-day lookback",
                f"Generated {selected_detail.reddit_panel.generated_at}",
            ]
        )
        st.write(selected_detail.reddit_panel.summary)
        st.caption(selected_detail.reddit_panel.methodology)
with social_columns[1]:
    with st.container(border=True):
        st.markdown("### Preview threads")
        if selected_detail.reddit_panel.posts:
            for post in selected_detail.reddit_panel.posts[:2]:
                st.markdown(f"**{post.title}**")
                st.write(post.excerpt)
                st.caption(f"Sentiment: {post.sentiment} | Source: {post.subreddit}")
        else:
            placeholder_card(
                "Social preview pending",
                "This city does not have a fuller thread preview yet, but the city profile still carries the base social signal.",
                "Planned: richer city-level thread clustering and freshness comparisons.",
            )

render_section_header(
    "Future watchlist",
    "Coming soon",
    "These placeholders mark the next product surfaces without pretending they already exist. They make the roadmap visible on the page and give the home experience a fuller product shape.",
)
watchlist_columns = st.columns(3)
with watchlist_columns[0]:
    placeholder_card(
        "Saved cities",
        "Build a personal shortlist and return to the same markets after you have changed your priorities or compared options with friends.",
        "Placeholder for watchlist persistence and profile saves.",
    )
with watchlist_columns[1]:
    placeholder_card(
        "Alerts and refreshes",
        "See when a city's score moves because rents, unemployment, safety inputs, or social sentiment changed materially.",
        "Placeholder for refresh jobs and score-change monitoring.",
    )
with watchlist_columns[2]:
    placeholder_card(
        "Weight presets",
        "Save modes like budget-first, career-max, or warm-weather reset so the home page feels reusable instead of one-off.",
        "Placeholder for saved preference profiles and onboarding flows.",
    )
