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
from wsis.ui.theme import inject_theme


st.set_page_config(page_title="WSIS | Decision", layout="wide")


BASELINE_SLUG = "chicago-il"
DEFAULT_OFFER_SALARY = 70_000
DEFAULT_MAX_RENT = 980


@st.cache_resource
def get_client() -> ApiCityClient:
    return ApiCityClient()


def current_weights() -> ScoreWeights:
    return score_weights_from_state(st.session_state)


def load_details(_client: ApiCityClient, weights: ScoreWeights) -> list[CityDetail]:
    summaries, list_source = _client.list_cities(weights)
    details: list[CityDetail] = []
    for summary in summaries:
        detail, _ = _client.get_city(summary.slug, weights)
        details.append(detail)
    return details


def inject_styles() -> None:
    inject_theme()
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1120px;
            padding-top: 1.45rem;
            padding-bottom: 2.5rem;
        }
        .block-container * {
            box-sizing: border-box;
        }
        .decision-topline {
            color: #5b6470;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
        .decision-title {
            color: #17202a;
            font-size: 2rem;
            font-weight: 750;
            line-height: 1.05;
            margin: 0.15rem 0 0.25rem;
        }
        .decision-subtitle {
            color: #56616c;
            font-size: 0.98rem;
            margin: 0 0 1rem;
        }
        .case-strip {
            border-top: 1px solid #d8dee5;
            border-bottom: 1px solid #d8dee5;
            display: grid;
            gap: 0;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            margin: 0.75rem 0 1rem;
            max-width: 100%;
            overflow: hidden;
        }
        .case-cell {
            min-width: 0;
            padding: 0.72rem 0.8rem;
            border-right: 1px solid #e1e5ea;
        }
        .case-cell:last-child {
            border-right: 0;
        }
        .case-label {
            color: #66717d;
            font-size: 0.73rem;
            font-weight: 700;
            text-transform: uppercase;
        }
        .case-value {
            color: #1d2731;
            font-size: 0.95rem;
            font-weight: 650;
            margin-top: 0.14rem;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        .decision-grid {
            display: grid;
            gap: 1.2rem;
            grid-template-columns: minmax(260px, 0.78fr) minmax(0, 1.22fr);
            align-items: start;
        }
        .input-rail {
            background: rgba(255,255,255,0.78);
            border: 1px solid #dce5e8;
            border-radius: 18px;
            box-shadow: 0 16px 40px rgba(23, 33, 43, 0.06);
            padding: 1rem;
        }
        .section-label {
            color: #5b6470;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            margin: 0.2rem 0 0.55rem;
            text-transform: uppercase;
        }
        .verdict-band {
            border-left: 5px solid #a13f32;
            background: rgba(255,255,255,0.78);
            border-bottom: 1px solid #dce5e8;
            border-right: 1px solid #dce5e8;
            border-top: 1px solid #dce5e8;
            border-radius: 16px;
            box-shadow: 0 16px 40px rgba(23, 33, 43, 0.05);
            padding: 0.82rem 0.95rem;
            margin-bottom: 0.75rem;
            min-width: 0;
        }
        .verdict-band.take {
            border-left-color: #1f7a52;
        }
        .verdict-band.risky {
            border-left-color: #8a6822;
        }
        .verdict-band h2 {
            color: #18232c;
            font-size: 1.25rem;
            line-height: 1.22;
            margin: 0 0 0.25rem;
        }
        .verdict-band p {
            color: #53606b;
            font-size: 0.92rem;
            margin: 0;
        }
        .ledger {
            border-top: 1px solid #d9dee5;
            margin-bottom: 1rem;
            min-width: 0;
            overflow: hidden;
        }
        .ledger-row {
            border-bottom: 1px solid #e1e5ea;
            display: grid;
            gap: 0.75rem;
            grid-template-columns: 6.5rem minmax(8rem, 0.72fr) minmax(0, 1.28fr);
            padding: 0.68rem 0;
            align-items: start;
            min-width: 0;
        }
        .ledger-status {
            font-size: 0.74rem;
            font-weight: 800;
            text-transform: uppercase;
            overflow-wrap: anywhere;
        }
        .ledger-name {
            color: #1f2b34;
            font-size: 0.93rem;
            font-weight: 650;
            min-width: 0;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        .ledger-detail {
            color: #56616c;
            font-size: 0.88rem;
            min-width: 0;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        .status-pass { color: #1f7a52; }
        .status-fail { color: #a13f32; }
        .status-review, .status-weak, .status-missing, .status-seeded, .status-proxy {
            color: #8a6822;
        }
        .decision-note {
            border-left: 3px solid #8a6822;
            color: #4f5964;
            font-size: 0.9rem;
            margin: 0 0 0.9rem;
            padding-left: 0.65rem;
        }
        .context-line {
            color: #56616c;
            font-size: 0.9rem;
            margin: -0.15rem 0 1rem;
            overflow-wrap: anywhere;
        }
        .context-line strong {
            color: #1f2b34;
        }
        .empty-evidence {
            border-top: 1px solid #d9dee5;
            border-bottom: 1px solid #e1e5ea;
            color: #56616c;
            padding: 0.72rem 0;
        }
        .pass-plan {
            border: 1px solid #dce5e8;
            border-radius: 14px;
            background: rgba(255,255,255,0.78);
            box-shadow: 0 12px 32px rgba(23, 33, 43, 0.04);
            margin: 0 0 0.9rem;
            padding: 0.72rem 0.82rem;
        }
        .pass-plan ol {
            margin: 0;
            padding-left: 1.15rem;
        }
        .pass-plan li {
            color: #24303a;
            font-size: 0.9rem;
            line-height: 1.45;
            margin: 0.32rem 0;
        }
        div[data-testid="stForm"] {
            border: 0;
            padding: 0;
        }
        div[data-testid="stForm"] button {
            width: 100%;
        }
        .stToggle {
            margin-bottom: -0.2rem;
        }
        div[data-testid="stSelectbox"],
        div[data-testid="stNumberInput"],
        div[data-testid="stToggle"] {
            width: 100%;
        }
        div[data-testid="stSelectbox"] label,
        div[data-testid="stNumberInput"] label,
        div[data-testid="stToggle"] label,
        div[data-testid="stCheckbox"] label,
        div[data-testid="stSelectbox"] label p,
        div[data-testid="stNumberInput"] label p,
        div[data-testid="stToggle"] label p,
        div[data-testid="stCheckbox"] label p {
            color: #24303a !important;
            font-size: 0.92rem !important;
            font-weight: 650 !important;
            line-height: 1.35 !important;
            opacity: 1 !important;
        }
        div[data-testid="stSelectbox"] [aria-label],
        div[data-testid="stNumberInput"] [aria-label],
        div[data-testid="stToggle"] [aria-label],
        div[data-testid="stCheckbox"] [aria-label] {
            color: #24303a !important;
        }
        div[data-testid="stWidgetLabel"] p,
        div[data-testid="stMarkdownContainer"] p {
            color: #56616c;
        }
        div[data-testid="stSelectbox"] > div,
        div[data-testid="stNumberInput"] > div {
            width: 100%;
        }
        @media (max-width: 900px) {
            .block-container {
                max-width: 100%;
                padding-top: 1rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }
            .decision-topline {
                font-size: 0.72rem;
            }
            .decision-title {
                font-size: 1.55rem;
                line-height: 1.12;
                margin-top: 0.1rem;
            }
            .decision-subtitle {
                font-size: 0.9rem;
                margin-bottom: 0.8rem;
            }
            .case-strip {
                grid-template-columns: 1fr 1fr;
                margin-bottom: 0.85rem;
            }
            .case-cell {
                padding: 0.62rem 0.65rem;
            }
            .case-cell:nth-child(2) {
                border-right: 0;
            }
            .case-cell:nth-child(1), .case-cell:nth-child(2) {
                border-bottom: 1px solid #e1e5ea;
            }
            .case-label {
                font-size: 0.68rem;
            }
            .case-value {
                font-size: 0.88rem;
            }
            .decision-grid {
                grid-template-columns: 1fr;
            }
            .input-rail {
                border-radius: 14px;
                padding: 0.78rem;
            }
            .section-label {
                margin-top: 0.35rem;
            }
            .verdict-band {
                padding: 0.75rem 0.8rem;
            }
            .verdict-band h2 {
                font-size: 1.08rem;
            }
            .verdict-band p,
            .decision-note,
            .context-line,
            .empty-evidence,
            .pass-plan li {
                font-size: 0.86rem;
            }
            .ledger-row {
                gap: 0.24rem 0.65rem;
                grid-template-columns: minmax(4.7rem, 0.36fr) minmax(0, 1fr);
                padding: 0.62rem 0;
            }
            .ledger-status {
                font-size: 0.68rem;
                line-height: 1.35;
            }
            .ledger-name {
                font-size: 0.88rem;
                line-height: 1.35;
            }
            .ledger-detail {
                grid-column: 2;
                font-size: 0.84rem;
                line-height: 1.42;
            }
            div[data-testid="stSelectbox"],
            div[data-testid="stNumberInput"],
            div[data-testid="stToggle"] {
                margin-bottom: 0.35rem;
            }
            div[data-testid="stNumberInput"] input,
            div[data-baseweb="select"] {
                min-height: 2.75rem;
            }
        }
        @media (max-width: 390px) {
            .block-container {
                padding-left: 0.8rem;
                padding-right: 0.8rem;
            }
            .case-strip {
                grid-template-columns: 1fr;
            }
            .case-cell,
            .case-cell:nth-child(2) {
                border-right: 0;
                border-bottom: 1px solid #e1e5ea;
            }
            .case-cell:last-child {
                border-bottom: 0;
            }
            .ledger-row {
                grid-template-columns: minmax(4.25rem, 0.34fr) minmax(0, 1fr);
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_label(status: str) -> str:
    labels = {"pass": "Pass", "fail": "Fail", "review": "Review"}
    return labels.get(status, status.title())


def render_case_header(
    candidate: CityDetail,
    baseline: CityDetail,
    offer_salary: float,
    max_rent: float,
) -> None:
    st.html(
        f"""
        <div class="decision-topline">WSIS decision case</div>
        <div class="decision-title">Move decision, not city ranking.</div>
        <div class="decision-subtitle">Hard constraints decide the verdict. Weak evidence gets flagged separately.</div>
        <div class="case-strip">
          <div class="case-cell">
            <div class="case-label">Candidate</div>
            <div class="case-value">{html.escape(city_label(candidate))}</div>
          </div>
          <div class="case-cell">
            <div class="case-label">Baseline</div>
            <div class="case-value">{html.escape(city_label(baseline))}</div>
          </div>
          <div class="case-cell">
            <div class="case-label">Offer</div>
            <div class="case-value">${offer_salary:,.0f}</div>
          </div>
          <div class="case-cell">
            <div class="case-label">Rent ceiling</div>
            <div class="case-value">${max_rent:,.0f}</div>
          </div>
        </div>
        """,
    )


def render_verdict(summary: DecisionSummary) -> None:
    st.html(
        f"""
        <div class="verdict-band {html.escape(summary.verdict)}">
          <h2>{html.escape(summary.headline)}</h2>
          <p>{html.escape(summary.subhead)}</p>
        </div>
        """,
    )
    if summary.no_rent_match:
        st.html('<div class="decision-note">No candidate city in the current dataset meets this rent ceiling.</div>')


def render_constraint_ledger(summary: DecisionSummary) -> None:
    rows = []
    for check in summary.checks:
        status = status_label(check.status)
        rows.append(
            f"""
            <div class="ledger-row">
              <div class="ledger-status status-{html.escape(check.status)}">{html.escape(status)}</div>
              <div class="ledger-name">{html.escape(check.label)}<br>{html.escape(check.value)}</div>
              <div class="ledger-detail">{html.escape(check.detail)}</div>
            </div>
            """
        )
    st.html(f'<div class="ledger">{"".join(rows)}</div>')


def render_context(candidate: CityDetail, baseline: CityDetail) -> None:
    rent_delta = candidate.metrics.median_rent - baseline.metrics.median_rent
    temp_detail = "temperature data missing"
    if candidate.metrics.avg_temp_f is not None and baseline.metrics.avg_temp_f is not None:
        temp_delta = candidate.metrics.avg_temp_f - baseline.metrics.avg_temp_f
        temp_detail = f"{temp_delta:+.0f}F average temperature"

    st.html(
        f"""
        <div class="context-line">
          <strong>Baseline stays fixed:</strong>
          {html.escape(city_label(candidate))} is {html.escape(signed_money(rent_delta))} / mo vs Chicago and {html.escape(temp_detail)}.
        </div>
        """,
    )


def render_evidence(summary: DecisionSummary) -> None:
    if not summary.evidence_issues:
        st.html('<div class="empty-evidence">No skeptic flags for this run. Verify sources before acting.</div>')
        return

    rows = []
    for issue in summary.evidence_issues:
        rows.append(
            f"""
            <div class="ledger-row">
              <div class="ledger-status status-{html.escape(issue.flag)}">{html.escape(issue.flag)}</div>
              <div class="ledger-name">{html.escape(issue.title)}</div>
              <div class="ledger-detail">{html.escape(issue.detail)}</div>
            </div>
            """
        )
    st.html(f'<div class="ledger">{"".join(rows)}</div>')


def render_pass_plan(summary: DecisionSummary) -> None:
    items = "".join(f"<li>{html.escape(action)}</li>" for action in summary.pass_actions)
    st.html(f'<div class="pass-plan"><ol>{items}</ol></div>')


def render_section_label(label: str) -> None:
    st.html(f'<div class="section-label">{html.escape(label)}</div>')


def render_inputs(candidate_options: list[CityDetail], details_by_slug: dict[str, CityDetail]):
    render_section_label("Situation")
    candidate_slug = st.selectbox(
        "Candidate",
        [detail.summary.slug for detail in candidate_options],
        index=0,
        format_func=lambda slug: city_label(details_by_slug[slug]),
    )
    offer_salary = st.number_input(
        "Offer salary",
        min_value=1,
        max_value=500_000,
        value=DEFAULT_OFFER_SALARY,
        step=2_500,
    )
    max_rent = st.number_input(
        "Max rent",
        min_value=1,
        max_value=10_000,
        value=DEFAULT_MAX_RENT,
        step=50,
    )
    require_warmer = st.toggle(
        "Warmer than Chicago",
        value=True,
        help="Require the candidate city to have a warmer average temperature than Chicago.",
    )
    require_civic_fit = st.toggle(
        "Civic fit required",
        value=False,
        help="Require the candidate city to pass the civic-fit evidence check.",
    )
    require_downtown_fit = st.toggle(
        "Downtown fit required",
        value=False,
        help="Require the candidate city to pass the downtown-fit evidence check.",
    )
    return candidate_slug, offer_salary, max_rent, require_warmer, require_civic_fit, require_downtown_fit


inject_styles()
client = get_client()
weights = current_weights()
details = load_details(client, weights)
details_by_slug = {detail.summary.slug: detail for detail in details}

if BASELINE_SLUG not in details_by_slug:
    st.error("Chicago baseline is not available in the current city dataset.")
    st.stop()

baseline = details_by_slug[BASELINE_SLUG]
candidate_options = [detail for detail in details if detail.summary.slug != BASELINE_SLUG]
if not candidate_options:
    st.error("No candidate cities are available to compare against Chicago.")
    st.stop()

input_column, output_column = st.columns([0.76, 1.24], gap="large")

with input_column:
    with st.container(border=True):
        (
            candidate_slug,
            offer_salary,
            max_rent,
            require_warmer,
            require_civic_fit,
            require_downtown_fit,
        ) = render_inputs(candidate_options, details_by_slug)

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

with output_column:
    render_case_header(candidate, baseline, float(offer_salary), float(max_rent))
    render_section_label("Verdict")
    render_verdict(decision)
    render_section_label("Constraints")
    render_constraint_ledger(decision)
    render_section_label("What would make this pass?")
    render_pass_plan(decision)
    render_context(candidate, baseline)
    render_section_label("Sarah checks")
    render_evidence(decision)

    render_section_label("Evidence")
    with st.expander("Evidence used"):
        for point in decision.proof_points:
            st.write(f"- {point}")
