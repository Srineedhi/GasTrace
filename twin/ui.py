"""Small Streamlit/HTML helpers (pills, KPI tiles, figure embedding)."""

from __future__ import annotations

import base64
import io
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


# ------------------------------- UI helpers ----------------------------------
def H(s: str) -> str:
    """Collapse multi-line HTML to one line so Markdown never treats it as code."""
    return "".join(line.strip() for line in s.splitlines() if line.strip())


def md(s: str) -> None:
    st.markdown(H(s), unsafe_allow_html=True)


def show_df(df: pd.DataFrame) -> None:
    try:
        st.dataframe(df, width="stretch", hide_index=True)
    except Exception:  # older Streamlit versions
        st.dataframe(df, use_container_width=True, hide_index=True)


def pill(text: str, kind: str = "blue") -> str:
    return f"<span class='pill {kind}'><span class='dot'></span>{text}</span>"


def kpi(label: str, value: str, sub: str = "", kind: str = "") -> str:
    return (f"<div class='kpi {kind}'><div class='kpi-label'>{label}</div>"
            f"<div class='kpi-value'>{value}</div><div class='kpi-sub'>{sub}</div></div>")


def kpi_row(items: list[str]) -> None:
    md(f"<div class='kpi-row'>{''.join(items)}</div>")


def callout(text: str, kind: str = "info") -> None:
    md(f"<div class='callout {kind}'>{text}</div>")


def cardinal(deg: float) -> str:
    names = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
             "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return names[int((float(deg) % 360.0) / 22.5 + 0.5) % 16]


def wind_label(u: float) -> str:
    for limit, name in ((0.5, "Calm"), (1.6, "Light air"), (3.4, "Light breeze"), (5.5, "Gentle breeze"),
                        (8.0, "Moderate breeze"), (10.8, "Fresh breeze")):
        if u < limit:
            return name
    return "Strong breeze"


def level_of(reading: float, threshold: float) -> tuple[str, str]:
    if reading >= threshold:
        return "red", "ALARM"
    if reading >= 0.5 * threshold:
        return "amber", "WARN"
    return "green", "NORMAL"


def fig_img(fig, dpi: int = 150) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"<img class='map-img' alt='plot' src='data:image/png;base64,{b64}'/>"


def hud(inner: str, title: str, right: str = "") -> str:
    return (f"<div class='hud'><div class='hud-head'><span class='hud-title'>{title}</span>"
            f"<span class='hud-right'>{right}</span></div>{inner}</div>")
