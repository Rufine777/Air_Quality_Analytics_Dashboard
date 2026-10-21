"""Shared UI helpers: theme, typography, and chart defaults.

Import and call ``apply_theme()`` once near the top of each page (after
``st.set_page_config``) so every screen shares one look.
"""

import streamlit as st

# Dark, restrained palette with a single cool accent.
PALETTE = {
    "primary": "#38bdf8",
    "primary_dark": "#0ea5e9",
    "text": "#e5e7eb",
    "muted": "#94a3b8",
    "surface": "#111827",
    "surface_alt": "#0b1220",
    "border": "#1f2937",
    "accent": "#a78bfa",
}

_CSS = f"""
<style>
html, body, [class*="css"] {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue",
                 Arial, "Noto Sans", sans-serif;
    color: {PALETTE["text"]};
}}
h1, h2, h3, h4 {{
    letter-spacing: -0.01em;
    font-weight: 600;
    color: {PALETTE["text"]};
}}
h1 {{ font-size: 1.75rem; margin-bottom: 0.25rem; }}
h2 {{ font-size: 1.25rem; margin-top: 1.25rem; }}
h3 {{ font-size: 1.05rem; }}

.block-container {{
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1280px;
}}

[data-testid="stMetric"] {{
    background: {PALETTE["surface"]};
    border: 1px solid {PALETTE["border"]};
    border-radius: 10px;
    padding: 0.75rem 1rem;
}}
[data-testid="stMetricLabel"] {{
    color: {PALETTE["muted"]};
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
[data-testid="stMetricValue"] {{
    font-size: 1.5rem;
    font-weight: 600;
    color: {PALETTE["text"]};
}}

section[data-testid="stSidebar"] {{
    background: {PALETTE["surface_alt"]};
    border-right: 1px solid {PALETTE["border"]};
}}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{
    font-size: 0.95rem;
}}

button[data-baseweb="tab"] {{
    font-weight: 500;
    color: {PALETTE["muted"]};
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: {PALETTE["primary"]};
}}

div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 12px;
    border-color: {PALETTE["border"]};
    background: {PALETTE["surface"]};
}}

button[kind="primary"], .stButton > button {{
    border-radius: 8px;
}}
.stDownloadButton > button {{
    border-radius: 8px;
}}

[data-testid="stDataFrame"] {{
    border: 1px solid {PALETTE["border"]};
    border-radius: 8px;
    overflow: hidden;
}}

footer {{ visibility: hidden; height: 0; }}
#MainMenu {{ visibility: hidden; }}

/* subtle gradient backdrop on main canvas */
[data-testid="stAppViewContainer"] {{
    background: radial-gradient(1200px 600px at 10% -10%, #13203a 0%, #0b1220 60%);
}}
</style>
"""


def apply_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def chart_layout(fig, title: str | None = None):
    fig.update_layout(
        template="plotly_dark",
        title=dict(text=title, x=0.02, xanchor="left", font=dict(size=14, color=PALETTE["text"])),
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", size=12, color=PALETTE["text"]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        colorway=["#38bdf8", "#a78bfa", "#34d399", "#fbbf24", "#f87171", "#60a5fa"],
    )
    fig.update_xaxes(showgrid=False, linecolor=PALETTE["border"], tickcolor=PALETTE["muted"])
    fig.update_yaxes(gridcolor="#1f2937", linecolor=PALETTE["border"], tickcolor=PALETTE["muted"])
    return fig