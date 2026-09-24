import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Mannheim Depot Optimizer",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# FILE PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent
FRONTEND_HTML = ROOT / "index.html"


# ============================================================
# STREAMLIT SIDEBAR
# ============================================================

st.sidebar.title("🚚 Mannheim Depot")
st.sidebar.caption("Planning Workspace")

page = st.sidebar.radio(
    "Navigation",
    [
        "🗺️ Live Map & Driver Planning",
        "🧠 Python Optimizer (OR-Tools)",
    ],
    label_visibility="collapsed",
)

st.sidebar.divider()

st.sidebar.caption(
    "Mannheim Depot Optimizer"
)


# ============================================================
# LIVE MAP
# ============================================================

if page == "🗺️ Live Map & Driver Planning":

    if not FRONTEND_HTML.exists():
        st.error(
            "index.html was not found in the project root."
        )
        st.stop()

    html_source = FRONTEND_HTML.read_text(
        encoding="utf-8"
    )

    components.html(
        html_source,
        height=1200,
        scrolling=True,
    )


# ============================================================
# PYTHON OPTIMIZER
# ============================================================

else:

    try:
        from optimizer_page import render_optimizer

        render_optimizer()

    except Exception as error:

        st.error(
            "Unable to load the Python optimizer."
        )

        st.exception(error)
