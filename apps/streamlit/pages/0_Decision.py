from __future__ import annotations

import html

import streamlit as st

from wsis.core.weights import score_weights_from_state
from wsis.domain.models import CityDetail, ScoreWeights
from wsis.services.api_client import ApiCityClient
from wsis.ui.decision_copy import (
    DecisionSummary,
    build_decision_summary,
    city_label,
    signed_money,
)


st.set_page_config(page_title="WSIS | Decision", layout="centered")


BASELINE_SLUG = "chicago-il"
DEFAULT_OFFER_SALARY = 70_000
DEFAULT_MAX_RENT = 980


@st.cache_resource
def get_client() -> ApiCityClient:
    return ApiCityClient()


def current_weights() -> ScoreWeights:
    return score_weights_from_state(st.session_state)


def load_details(_client: ApiCityClient, weights: ScoreWeights) -> tuple[list[CityDetail], str]:
    summaries, list_source = _client.list_cities(weights)
    details: list[CityDetail] = []
    sources = {list_source}
    for summary in summaries:
        detail, source = _client.get_city(summary.slug, weights)
        details.append(detail)
        sources.add(source)
    return details, ", ".join(sorted(sources))


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stHorizontalBlock"] {
            gap: 0.75rem;
        }
        .decision-step {
            color: #5f6f69;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            margin: 0.35rem 0 0.1rem;
            text-transform: uppercase;
        }
        .verdict {
            border: 1px solid rgba(46, 80, 72, 0.18);
            border-radius: 8px;
            padding: 0.85rem 0.95rem;
            margin: 0.6rem 0 0.7rem;
            background: #f8faf8;
        }
        .verdict h3 {
            margin: 0 0 0.25rem;
            color: #1d2b27;
            font-size: 1.18rem;
            line-height: 1.25;
        }
        .verdict p {
            margin: 0;
            color: #4d5b56;
            font-size: 0.92rem;
        }
        .check-card, .evidence-card, .context-card {
            border: 1px solid rgba(82, 96, 91, 0.16);
            border-radius: 8px;
            padding: 0.72rem 0.8rem;
            margin-bottom: 0.5rem;
            background: #ffffff;
        }
        .card-kicker {
            color: #6d7772;
            font-size: 0.76rem;
            font-weight: 700;
            text-transform: uppercase;
        }
        .check-card strong, .evidence-card strong, .context-card strong {
            display: block;
            color: #202c28;
            margin-top: 0.08rem;
        }
        .card-detail {
            color: #56635f;
            font-size: 0.88rem;
            margin-top: 0.16rem;
        }
        .status-pass { color: #1f7a52; }
        .status-fail { color: #a13f32; }
        .status-review { color: #8a6822; }
        .decision-note {
            border-left: 3px solid #8a6822;
            color: #4e5a55;
            padding-left: 0.7rem;
            font-size: 0.9rem;
            margin: 0.4rem 0 0.75rem;
        }
        @media (max-width: 640px) {
            .verdict, .check-card, .evidence-card, .context-card {
                padding: 0.7rem;
            }
            .verdict h3 {
                font-size: 1.05rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_label(status: str) -> str:
    labels = {"pass": "Pass", "fail": "Fail", "review": "Review"}
    return labels.get(status, status.title())


def render_step(label: str) -> None:
    st.markdown(f'<div class="decision-step">{html.escape(label)}</div>', unsafe_allow_html=True)


def render_verdict(summary: DecisionSummary) -> None:
    st.markdown(
        f"""
        <div class="verdict">
          <h3>{html.escape(summary.headline)}</h3>
          <p>{html.escape(summary.subhead)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if summary.no_rent_match:
        st.markdown(
            '<div class="decision-note">No city in the current dataset meets this rent ceiling.</div>',
            unsafe_allow_html=True,
        )


def render_check_cards(summary: DecisionSummary) -> None:
    for check in summary.checks:
        status_class = f"status-{check.status}"
        st.markdown(
            f"""
            <div class="check-card">
              <div class="card-kicker {status_class}">{html.escape(status_label(check.status))}</div>
              <strong>{html.escape(check.label)} · {html.escape(check.value)}</strong>
              <div class="card-detail">{html.escape(check.detail)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_context(candidate: CityDetail, baseline: CityDetail, source: str) -> None:
    rent_delta = candidate.metrics.median_rent - baseline.metrics.median_rent
    temp_detail = "Missing temperature"
    if candidate.metrics.avg_temp_f is not None and baseline.metrics.avg_temp_f is not None:
        temp_delta = candidate.metrics.avg_temp_f - baseline.metrics.avg_temp_f
        temp_detail = f"{temp_delta:+.0f}F average temperature"

    st.markdown(
        f"""
        <div class="context-card">
          <div class="card-kicker">Context only</div>
          <strong>Chicago baseline stays fixed.</strong>
          <div class="card-detail">
            {html.escape(city_label(candidate))}: {html.escape(signed_money(rent_delta))} / mo vs Chicago · {html.escape(temp_detail)}
          </div>
          <div class="card-detail">Data path: {html.escape(source)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_evidence(summary: DecisionSummary) -> None:
    if not summary.evidence_issues:
        st.markdown(
            """
            <div class="evidence-card">
              <div class="card-kicker status-pass">Sarah</div>
              <strong>No skeptic flags for this run.</strong>
              <div class="card-detail">Still verify sources before acting on the offer.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for issue in summary.evidence_issues:
        st.markdown(
            f"""
            <div class="evidence-card">
              <div class="card-kicker">Sarah · {html.escape(issue.flag)}</div>
              <strong>{html.escape(issue.title)}</strong>
              <div class="card-detail">{html.escape(issue.detail)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


inject_styles()
client = get_client()
weights = current_weights()
details, source = load_details(client, weights)
details_by_slug = {detail.summary.slug: detail for detail in details}

if BASELINE_SLUG not in details_by_slug:
    st.error("Chicago baseline is not available in the current city dataset.")
    st.stop()

baseline = details_by_slug[BASELINE_SLUG]
candidate_options = [detail for detail in details if detail.summary.slug != BASELINE_SLUG]
if not candidate_options:
    st.error("No candidate cities are available to compare against Chicago.")
    st.stop()

st.title("Decision")

with st.container():
    render_step("1. Situation")
    st.caption("Baseline: Chicago, IL")
    candidate_slug = st.selectbox(
        "Candidate",
        [detail.summary.slug for detail in candidate_options],
        index=0,
        format_func=lambda slug: city_label(details_by_slug[slug]),
    )
    left, right = st.columns(2)
    with left:
        offer_salary = st.number_input(
            "Offer salary",
            min_value=1,
            max_value=500_000,
            value=DEFAULT_OFFER_SALARY,
            step=2_500,
        )
    with right:
        max_rent = st.number_input(
            "Max rent",
            min_value=1,
            max_value=10_000,
            value=DEFAULT_MAX_RENT,
            step=50,
        )
    require_warmer = st.toggle("Warmer than Chicago", value=True)
    require_civic_fit = st.toggle("Civic fit required", value=False)
    require_downtown_fit = st.toggle("Downtown fit required", value=False)

candidate = details_by_slug[candidate_slug]
decision = build_decision_summary(
    candidate=candidate,
    baseline=baseline,
    all_details=details,
    offer_salary=float(offer_salary),
    max_rent=float(max_rent),
    require_warmer=require_warmer,
    require_civic_fit=require_civic_fit,
    require_downtown_fit=require_downtown_fit,
)

render_step("2. Verdict")
render_verdict(decision)
render_check_cards(decision)
render_context(candidate, baseline, source)

render_step("3. Sarah checks")
render_evidence(decision)

with st.expander("Evidence used"):
    for point in decision.proof_points:
        st.write(f"- {point}")
