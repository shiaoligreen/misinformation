"""
Linguistic Misinformation Markers:  Streamlit App

Run this with:  streamlit run linguistic_markers_app.py

"""

from pathlib import Path

import streamlit as st
import requests

from templates import render_card, render_combined_card, render_bar_chart


# PAGE CONFIG — this has to be the first call

st.set_page_config(
    page_title="Linguistic Misinformation Markers",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# CSS — loaded from styles.css and inserted via st.markdown

css = Path(__file__).parent / "styles.css"
st.markdown(f"<style>{css.read_text()}</style>", unsafe_allow_html=True)


# BACKEND call to fastapi
import os
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


ALL_TAGS = ["ADJECTIVES", "ALL_CAPS", "EXCLAMATION_MARKS", "HEDGING", "UNK"]



def _to_entry(result: dict) -> dict:
    """Convert a backend result dict to the app's entry format."""
    tags_lower = result["tags"].split() if result["tags"] else []
    raw_tags = result.get("raw_tags", {})
    tag_words = {
        tag_lower.upper(): [
            item[0] if isinstance(item, list) else item
            for item in items
        ]
        for tag_lower, items in raw_tags.items()
    }
    return {
        "id":        result["doc_id"],
        "text":      result["raw_text"],
        "tags":      [t.upper() for t in tags_lower],
        "tag_words": tag_words,
    }


def call_backend(query: str, annotated_only: bool = True, show_ai: bool = False) -> tuple[list[dict], list[dict]]:
    """Call the backend /search endpoint and return (main_results, ai_results) in app format."""
    params = {
        "query":   query,
        "source":  "annotated" if annotated_only else "all",
        "show_ai": show_ai,
    }
    try:
        resp = requests.get(f"{BACKEND_URL}/search", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Backend unavailable: {e}")
        return [], []
    return (
        [_to_entry(r) for r in data.get("main_results", [])],
        [_to_entry(r) for r in data.get("ai_results", [])],
    )



# SESSION STATE  — persists across re-runs

if "active_tags" not in st.session_state:
    st.session_state.active_tags = set()
if "search_query" not in st.session_state:
    st.session_state.search_query = "terrifying"


# HEADER

col_title, col_badge = st.columns([5, 1])

with col_title:
    st.markdown(
        '<div class="header-title">Linguistic <em>Misinformation Markers</em></div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="header-meta">'
        'Search over 1 million examples'
        '<span>·</span> 5 human annotators'
        '<span>·</span> 1 AI annotator'
        '<span>·</span> 1,000 annotated examples'
        '</div>',
        unsafe_allow_html=True,
    )

with col_badge:
    st.markdown(
        '<div style="padding-top:6px; display:flex; flex-direction:column; gap:4px; align-items:flex-start;">'
        '<span style="font-family:\'EB Garamond\',serif; font-size:1.1rem; font-style:italic; font-weight:600; color:#c0392b;">Fleiss\'s κ</span>'
        '<span style="font-family:\'JetBrains Mono\',monospace; font-size:0.78rem; color:#999;">Humans only &nbsp; 0.739</span>'
        '<span style="font-family:\'JetBrains Mono\',monospace; font-size:0.78rem; color:#999;">Humans + AI &nbsp; 0.575</span>'
        '</div>',
        unsafe_allow_html=True,
    )

st.markdown("<hr style='border:none;border-top:1px solid #e0e0e0;margin:12px 0 20px;'>", unsafe_allow_html=True)


# SEARCH BAR

search_col, btn_col = st.columns([5, 1])

with search_col:
    query = st.text_input(
        label="Search query",
        value=st.session_state.search_query,
        placeholder="Search terms...",
        key="search_input",
        label_visibility="collapsed",
    )

with btn_col:
    search_clicked = st.button("SEARCH", use_container_width=True)

chk_col1, chk_col2, _ = st.columns([1, 2, 3])
with chk_col1:
    annotated_only = st.checkbox("Annotated examples only", value=True)
with chk_col2:
    show_ai = st.checkbox("Show AI (Gemini) annotations", value=False)

if search_clicked or query != st.session_state.search_query:
    st.session_state.search_query = query
    
    st.session_state.active_tags = set()


# SEARCH

all_results, ai_results = call_backend(st.session_state.search_query, annotated_only, show_ai)

active_tags = st.session_state.active_tags
if not active_tags:
    filtered = all_results
else:
    filtered = [r for r in all_results if any(t in r["tags"] for t in active_tags)]


# RESULTS COUNT + TAG FILTER BUTTONS

st.markdown(
    f'<div style="font-size:0.88rem; color:#555; margin:12px 0 8px;">'
    f'<b style="color:#c0392b">{len(filtered)}</b> results for '
    f'<b>"{st.session_state.search_query}"</b></div>',
    unsafe_allow_html=True,
)

st.markdown('<div style="font-size:0.72rem; color:#888; font-weight:700; letter-spacing:0.1em; margin-bottom:6px;">HIGHLIGHT AND FILTER BY TAG:</div>', unsafe_allow_html=True)

_TAG_ACTIVE_COLORS = {
    "ALL":               "#111111",
    "ALL_CAPS":          "#e67e22",
    "EXCLAMATION_MARKS": "#c0392b",
    "HEDGING":           "#27ae60",
    "ADJECTIVES":        "#2980b9",
    "UNK":               "#8e44ad",
}

all_filter_tags = ["ALL"] + ALL_TAGS

_css_rules = []
for _i, _t in enumerate(all_filter_tags):
    _is_active = (len(st.session_state.active_tags) == 0) if _t == "ALL" else (_t in st.session_state.active_tags)
    if _is_active:
        _color = _TAG_ACTIVE_COLORS.get(_t, "#111111")
        _nth = _i + 1
        # Only the tag-filter row has primary-type buttons, so nth-child on stColumn
        # within any stHorizontalBlock safely targets only our buttons.
        _sel = f'[data-testid="stHorizontalBlock"] [data-testid="stColumn"]:nth-child({_nth})'
        _css_rules.append(
            f'{_sel} button[kind="primary"] {{background:{_color} !important; border-color:{_color} !important;}}'
            f'{_sel} button[kind="primary"]:hover {{background:{_color}cc !important; border-color:{_color}cc !important;}}'
        )

if _css_rules:
    st.markdown(f"<style>{''.join(_css_rules)}</style>", unsafe_allow_html=True)

tag_cols = st.columns(len(all_filter_tags), gap="small")

for i, t in enumerate(all_filter_tags):
    with tag_cols[i]:
        if t == "ALL":
            is_active = len(st.session_state.active_tags) == 0
        else:
            is_active = t in st.session_state.active_tags
        if st.button(t, key=f"tag_btn_{t}", use_container_width=True,
                     type="primary" if is_active else "secondary"):
            if t == "ALL":
                st.session_state.active_tags = set()
            elif t in st.session_state.active_tags:
                st.session_state.active_tags = st.session_state.active_tags - {t}
            else:
                st.session_state.active_tags = st.session_state.active_tags | {t}
            st.rerun()

# ANNOTATION TAGS LEGEND

st.markdown('<div style="font-size:0.72rem; color:#888; font-weight:700; letter-spacing:0.1em; margin-top:16px; margin-bottom:6px; border-top:1px solid #e0e0e0; padding-top:12px;">ANNOTATION TAGS</div>', unsafe_allow_html=True)

legend_items = [
    ("ADJECTIVES",        "#cce5ff", "#004085",
     'Adjectives with suffixes <code class="inline-code">-ful</code>, '
     '<code class="inline-code">-less</code>, <code class="inline-code">-ment</code>, '
     '<code class="inline-code">-ness</code>, <code class="inline-code">-ing</code>, or '
     '<code class="inline-code">-ible</code>.'),
    ("ALL_CAPS",          "#fde8c8", "#b5500a", "Capitalized words that are not acronyms."),
    ("EXCLAMATION_MARKS", "#fcd6d6", "#a01010", "Any number of exclamation marks."),
    ("HEDGING",           "#d4edda", "#1a6632", "Words found in the hedging lexicon."),
    ("UNK",               "#e2d4f0", "#5a2d82", "Profanity."),
]

_all_caps_combo_row = (
    '<div class="legend-row">'
    '<span class="legend-pill" style="background:#d4edda; color:#e67e22; font-weight:700;">ALL_CAPS + TAG</span>'
    '<span>Words matching all_caps plus another tag are shown in '
    '<span style="color:#e67e22; font-weight:700;">orange text</span> with the other tag\'s '
    'background colour.</span>'
    '</div>'
)

legend_rows = ""
for label, bg, fg, desc in legend_items:
    legend_rows += f'<div class="legend-row"><span class="legend-pill" style="background:{bg};color:{fg};">{label}</span><span>{desc}</span></div>'
    if label == "ALL_CAPS":
        legend_rows += _all_caps_combo_row

st.markdown(
    f'<div style="background:#f5f5f3; border-radius:6px; padding:16px 20px; margin:8px 0;">'
    f'<div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:0 24px;">{legend_rows}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f'<div style="text-align:right; font-size:0.72rem; color:#aaa; margin:8px 0;">'
    f'↕ scroll to see all {len(filtered)} results</div>',
    unsafe_allow_html=True,
)


# RESULT CARDS

if filtered:
    ai_by_text = {}
    if show_ai:
        ai_filtered = ai_results if not active_tags else [r for r in ai_results if any(t in r["tags"] for t in active_tags)]
        ai_by_text = {r["text"].strip().lower(): r for r in ai_filtered}

    for entry in filtered:
        if show_ai:
            ai_match = ai_by_text.get(entry["text"].strip().lower())
            if ai_match:
                st.markdown(render_combined_card(entry, ai_match, active_tags), unsafe_allow_html=True)
            else:
                st.markdown(render_card(entry, active_tags, source="Human"), unsafe_allow_html=True)
        else:
            st.markdown(render_card(entry, active_tags), unsafe_allow_html=True)
else:
    st.info("No results found. Try a different search term or filter.")


# TAG DISTRIBUTION BAR CHART

st.markdown("<hr style='border:none;border-top:1px solid #e0e0e0;margin:24px 0 0;'>", unsafe_allow_html=True)
st.markdown('<div class="subsection-title">Tag Distribution</div>', unsafe_allow_html=True)
st.markdown('<div class="subsection-desc">Frequency of each annotation tag across matching results.</div>', unsafe_allow_html=True)

tag_counts = {t: sum(1 for r in all_results if t in r["tags"]) for t in ALL_TAGS}

st.markdown(render_bar_chart(tag_counts), unsafe_allow_html=True)


