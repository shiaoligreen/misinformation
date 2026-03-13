# `linguistic_markers_app.py` — Streamlit Frontend

## Overview

The main entry point for the user-facing application. Renders the complete UI using Streamlit and communicates with the FastAPI backend (`be_fast.py`) over HTTP.

Run with:

```bash
streamlit run linguistic_markers_app.py
```

The app is then accessible at `http://localhost:8501`.

---

## Dependencies

| Import | Purpose |
|---|---|
| `pathlib.Path` | Resolves path to `styles.css` relative to this file |
| `streamlit` | UI framework — all rendering, widgets, and session state |
| `requests` | HTTP client for calling the FastAPI `/search` endpoint |
| `templates.render_card` | Generates highlighted result card HTML |
| `templates.render_bar_chart` | Generates tag distribution bar chart HTML |

---

## Configuration

### Backend URL

```python
BACKEND_URL = "http://localhost:8000"
```

All backend requests are issued to this base URL. The `/search` endpoint is appended at call time.

### Tag List

```python
ALL_TAGS = ["ALL_CAPS", "EXCLAMATION_MARKS", "HEDGING", "ADJECTIVES", "UNK"]
```

Defines the tag order used for filter buttons and the bar chart.

### Page Config

```python
st.set_page_config(
    page_title="Linguistic Misinformation Markers",
    layout="wide",
    initial_sidebar_state="collapsed",
)
```

Must be the **first** Streamlit call in the script.

### CSS Injection

`styles.css` is read from disk and injected into the page via `st.markdown()` on every re-run. This allows standard CSS classes to be used inside the raw HTML produced by `templates.py`.

---

## Session State

Streamlit re-runs the entire script on every user interaction. Session state is used for values across re-runs.

| Key | Initial Value | Purpose |
|---|---|---|
| `active_tag` | `"ALL"` | Tracks the currently selected tag filter button |
| `search_query` | `"terrifying"` | Tracks the last-submitted search term |

---

## Helper Functions

### `_to_entry(result) → dict`

Converts a raw backend result dict into the format expected by `templates.py`.

| Input key | Output key | Transformation |
|---|---|---|
| `doc_id` | `id` | Direct copy |
| `raw_text` | `text` | Direct copy |
| `tags` (space-separated str) | `tags` (list of uppercase str) | `.split()` then `.upper()` on each |
| `raw_tags` (dict of lowercase tag → span lists) | `tag_words` (dict of uppercase tag → word strings) | Keys uppercased; span lists `[word, start, end]` unpacked to just `word` |

---

### `call_backend(query, annotated_only, show_ai) → tuple[list, list]`

Issues a GET request to `BACKEND_URL/search` and returns `(main_results, ai_results)` in app format.

| Parameter | Type | Description |
|---|---|---|
| `query` | `str` | Search term |
| `annotated_only` | `bool` | If `True`, sets `source=annotated`; otherwise `source=all` |
| `show_ai` | `bool` | Passed directly to the backend as `show_ai` |

- On success: parses JSON response and converts each result via `_to_entry()`.
- On failure (`requests.exceptions.RequestException`): displays an error banner via `st.error()` and returns two empty lists. The app continues to render with zero results rather than crashing.

---

## UI Layout

The app renders top-to-bottom in a single column (wide layout). Each section re-renders on every Streamlit re-run.

### Header

Two-column layout:
- **Left:** App title and subtitle (1M examples, annotator counts).
- **Right:** Fleiss's κ scores for humans-only and humans + AI.

### Search Bar

Two-column layout:
- **Left:** `st.text_input` for the search query.
- **Right:** `SEARCH` button.

Two checkboxes below:
- **Annotated examples only** — controls the `source` parameter sent to the backend.
- **Show AI (Gemini) annotations** — triggers a parallel backend search and renders a second result section.

A search re-run is triggered when either the button is clicked or the query text changes.

### Tag Filter Buttons

One button per tag (`ALL`, `ALL_CAPS`, `EXCLAMATION_MARKS`, `HEDGING`, `ADJECTIVES`, `UNK`). The active button is styled using a dynamically injected CSS block keyed to `st.session_state.active_tag`. Clicking a button sets `active_tag` in session state and calls `st.rerun()`.

Client-side filtering is applied after the backend call:

```python
filtered = all_results if active_tag == "ALL" else [r for r in all_results if active_tag in r["tags"]]
```

### Result Cards

Each result in `filtered` is rendered via `templates.render_card(entry, active_tag)` and take `st.markdown(unsafe_allow_html=True)`. If no results match, an info message is shown.

### AI Results Section

Rendered only when `show_ai` is checked. Applies the same tag filter to `ai_results` and renders cards under a horizontal rule separator.

### Tag Distribution Bar Chart

Always rendered below the result cards. Counts are computed over the **unfiltered** `all_results` list (not `filtered`), so the chart always reflects the full search result distribution regardless of the active tag button.

```python
tag_counts = {t: sum(1 for r in all_results if t in r["tags"]) for t in ALL_TAGS}
```

Chart is rendered via `templates.render_bar_chart(tag_counts)`.

### Annotation Tags Legend

Static reference section at the bottom of the page. Lists all five tags with descriptions and colour swatches. The `ALL_CAPS + TAG` overlap rendering rule is also explained here with an inline example.

---

## Data Flow Summary

```
User interaction (widget change or button click)
    └── Streamlit re-runs entire script
        └── call_backend(query, annotated_only, show_ai)
            └── GET http://localhost:8000/search?query=...
                └── FastAPI → be_search.search() → Whoosh index
            └── Returns (main_results, ai_results)
        └── Client-side tag filter applied
        └── templates.render_card() → st.markdown() for each result
        └── templates.render_bar_chart() → st.markdown()
```
