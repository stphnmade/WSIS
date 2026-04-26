from __future__ import annotations

import html

import streamlit as st


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;650;750;800&family=Fraunces:opsz,wght@9..144,650;9..144,750&display=swap');

        :root {
            --wsis-ink: #17212b;
            --wsis-muted: #66717d;
            --wsis-line: #dce5e8;
            --wsis-paper: #fffdf8;
            --wsis-mint: #dff8ee;
            --wsis-sky: #e8f4ff;
            --wsis-sun: #fff0b8;
            --wsis-coral: #ff7a6b;
            --wsis-teal: #12a594;
            --wsis-blue: #5577ff;
            --wsis-plum: #7d5fff;
            --wsis-green: #23866f;
        }

        html, body, [class*="css"] {
            font-family: "Plus Jakarta Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 244, 229, 0.72), transparent 30rem),
                linear-gradient(180deg, #fffaf5 0%, #f9fbf8 54%, #fffaf5 100%);
            color: var(--wsis-ink);
        }

        section[data-testid="stSidebar"] {
            background: #fbf3eb;
            border-right: 1px solid #eadbd0;
        }

        section[data-testid="stSidebar"] * {
            color: #332b25;
        }

        section[data-testid="stSidebar"] a {
            border-radius: 10px;
            color: #332b25 !important;
            font-weight: 750;
        }

        section[data-testid="stSidebar"] a[aria-current="page"],
        section[data-testid="stSidebar"] a:hover {
            background: #f2dfd3 !important;
            color: #201815 !important;
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            color: var(--wsis-ink);
            letter-spacing: 0;
        }

        h1 {
            font-family: "Fraunces", "Plus Jakarta Sans", serif;
            font-size: clamp(2rem, 4.5vw, 4.2rem);
            line-height: 0.98;
        }

        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.74);
            border: 1px solid rgba(85, 119, 255, 0.14);
            border-radius: 14px;
            padding: 0.72rem 0.8rem;
            box-shadow: 0 8px 24px rgba(23, 33, 43, 0.05);
        }

        div[data-testid="stMetricLabel"] p {
            color: var(--wsis-muted);
            font-size: 0.78rem;
            font-weight: 750;
        }

        div[data-testid="stMetricValue"] {
            color: var(--wsis-ink);
            font-weight: 800;
        }

        div[data-baseweb="select"] > div {
            background: #fffdf8 !important;
            border-color: #dbcfc5 !important;
            color: var(--wsis-ink) !important;
        }

        div[data-baseweb="select"] span[data-baseweb="tag"] {
            background: #dff8ee !important;
            color: #173d38 !important;
            border: 1px solid rgba(18, 165, 148, 0.24) !important;
            border-radius: 10px !important;
            font-weight: 750 !important;
        }

        div[data-baseweb="select"] span[data-baseweb="tag"] span,
        div[data-baseweb="select"] span[data-baseweb="tag"] svg {
            color: #173d38 !important;
            fill: #173d38 !important;
        }

        div.stButton > button, div[data-testid="stBaseButton-secondary"] {
            border: 1px solid rgba(18, 165, 148, 0.28);
            border-radius: 999px;
            color: #12322f;
            font-weight: 750;
            min-height: 2.75rem;
            transition: transform 130ms ease, box-shadow 130ms ease, border-color 130ms ease;
            white-space: normal;
        }

        div[data-testid="stPageLink"] a,
        div[data-testid="stPageLink"] a p {
            color: #17212b !important;
            font-weight: 800 !important;
        }

        div[data-testid="stPageLink"] a {
            background: #ffffff !important;
            border: 1px solid #dbcfc5 !important;
            border-radius: 12px !important;
        }

        div[data-testid="stExpander"] details {
            border: 1px solid #eadbd0 !important;
            border-radius: 12px !important;
            overflow: hidden;
        }

        div[data-testid="stExpander"] summary {
            background: #fffaf5 !important;
            color: #17212b !important;
        }

        div[data-testid="stExpander"] summary * {
            color: #17212b !important;
        }

        div.stButton > button:hover {
            border-color: rgba(255, 122, 107, 0.55);
            box-shadow: 0 8px 20px rgba(255, 122, 107, 0.16);
            transform: translateY(-1px);
        }

        div[data-testid="stSelectbox"] label,
        div[data-testid="stMultiSelect"] label,
        div[data-testid="stNumberInput"] label {
            color: var(--wsis-muted);
            font-weight: 800;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.45rem;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            font-weight: 750;
            padding: 0.35rem 0.75rem;
        }

        .wsis-page-kicker {
            color: var(--wsis-teal);
            font-size: 0.78rem;
            font-weight: 850;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .wsis-page-title {
            font-family: "Fraunces", "Plus Jakarta Sans", serif;
            font-size: clamp(2rem, 4vw, 3.5rem);
            line-height: 1;
            margin: 0.12rem 0 0.35rem;
        }

        .wsis-page-subtitle {
            color: var(--wsis-muted);
            font-size: 1rem;
            line-height: 1.55;
            max-width: 62rem;
            margin-bottom: 1rem;
        }

        .wsis-panel {
            background: rgba(255, 255, 255, 0.76);
            border: 1px solid var(--wsis-line);
            border-radius: 18px;
            box-shadow: 0 16px 40px rgba(23, 33, 43, 0.06);
            padding: 1rem;
        }

        .wsis-soft-band {
            background:
                linear-gradient(120deg, rgba(223, 248, 238, 0.92), rgba(232, 244, 255, 0.9) 55%, rgba(255, 240, 184, 0.74));
            border: 1px solid rgba(18, 165, 148, 0.18);
            border-radius: 22px;
            padding: 1rem;
        }

        .wsis-mini-grid {
            display: grid;
            gap: 0.65rem;
            grid-template-columns: repeat(auto-fit, minmax(9.5rem, 1fr));
        }

        .wsis-mini-cell {
            background: rgba(255, 255, 255, 0.7);
            border: 1px solid rgba(23, 33, 43, 0.08);
            border-radius: 14px;
            padding: 0.72rem 0.78rem;
        }

        .wsis-mini-label {
            color: var(--wsis-muted);
            font-size: 0.72rem;
            font-weight: 850;
            text-transform: uppercase;
        }

        .wsis-mini-value {
            color: var(--wsis-ink);
            font-size: 1.05rem;
            font-weight: 850;
            margin-top: 0.12rem;
        }

        .wsis-pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin: 0.5rem 0;
        }

        .wsis-pill {
            background: #ffffff;
            border: 1px solid rgba(18, 165, 148, 0.22);
            border-radius: 999px;
            color: #20413c;
            display: inline-flex;
            font-size: 0.8rem;
            font-weight: 750;
            max-width: 100%;
            overflow-wrap: anywhere;
            padding: 0.32rem 0.68rem;
            white-space: normal;
        }

        @media (max-width: 900px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 1rem;
            }

            .wsis-panel, .wsis-soft-band {
                border-radius: 14px;
                padding: 0.78rem;
            }

            div[data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
                gap: 0.75rem;
            }

            div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
                flex: 1 1 100% !important;
                min-width: 0 !important;
                width: 100% !important;
            }

            div[data-testid="stDataFrame"],
            div[data-testid="stPlotlyChart"] {
                max-width: 100%;
                overflow-x: auto;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(kicker: str, title: str, subtitle: str) -> None:
    st.html(
        f"""
        <div class="wsis-page-kicker">{html.escape(kicker)}</div>
        <div class="wsis-page-title">{html.escape(title)}</div>
        <div class="wsis-page-subtitle">{html.escape(subtitle)}</div>
        """,
    )


def render_pills(labels: list[str]) -> None:
    if not labels:
        return
    items = "".join(f'<span class="wsis-pill">{html.escape(label)}</span>' for label in labels)
    st.html(f'<div class="wsis-pill-row">{items}</div>')


def render_metric_strip(items: list[tuple[str, str]]) -> None:
    if not items:
        return
    columns = st.columns(min(len(items), 4))
    for column, (label, value) in zip(columns * ((len(items) // len(columns)) + 1), items):
        with column:
            with st.container(border=True):
                st.caption(label)
                st.markdown(f"**{value}**")
