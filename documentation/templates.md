# `templates.py` — HTML Rendering Helpers

## Overview

Provides pure-Python functions that generate raw HTML strings for the Streamlit frontend. Visualisations are built here and injected into the page via `st.markdown(unsafe_allow_html=True)`.

This module has no dependencies on FastAPI or `be_search` — it operates solely on data dicts passed in from `linguistic_markers_app.py`.

---

## Dependencies

| Import | Purpose |
|---|---|
| `re` | Regex matching for locating annotation spans within display text |

---

## Constants

### `BAR_COLORS`

Maps annotation tag names to hex colour codes used in the bar chart bars.

| Tag | Colour |
|---|---|
| `ALL_CAPS` | `#e67e22` (orange) |
| `EXCLAMATION_MARKS` | `#c0392b` (red) |
| `HEDGING` | `#27ae60` (green) |
| `ADJECTIVES` | `#2980b9` (blue) |
| `UNK` | `#8e44ad` (purple) |

### `TAG_CSS`

Maps tag names to CSS class names applied to highlighted `<span>` elements in result cards. These classes must be defined in `styles.css`.

| Tag | CSS Class |
|---|---|
| `ALL_CAPS` | `hl-orange` |
| `EXCLAMATION_MARKS` | `hl-red` |
| `HEDGING` | `hl-green` |
| `ADJECTIVES` | `hl-blue` |
| `UNK` | `hl-purple` |

### `TAG_BG`

Maps secondary tag names to light background tint hex codes. Used only in the `ALL_CAPS` overlap case (see `compute_highlights` below).

---

## Functions

### `compute_highlights(text, active_tag, tag_words) → str`

Wraps annotated words in the display text with styled `<span>` elements.

| Parameter | Type | Description |
|---|---|---|
| `text` | `str` | Raw display text for one corpus example |
| `active_tag` | `str` | Currently selected tag filter button: `"ALL"` or a specific tag name |
| `tag_words` | `dict` | Maps tag name → list of matched word strings from annotation data |

**Behaviour:**

- When `active_tag == "ALL"`: all tags are highlighted simultaneously.
- When a specific tag is selected: only words matching that tag are highlighted.
- Overlap case — `ALL_CAPS` + another tag: the word is rendered with **orange text** on the secondary tag's light background tint, rather than using the standard CSS class. This is handled inline via a `style` attribute since it requires combining two tag signals.

**Process:**

1. Collects all `(start, end)` character spans for each applicable tag using `re.finditer`.
2. Sorts spans by start position and iterates through them left to right.
3. Overlapping spans (where `start < pos`) are skipped to avoid double-wrapping.
4. Builds the result string by interleaving plain text segments with highlighted `<span>` blocks.

**Returns:** HTML string of the full text with `<span>` elements inserted at annotated positions.

---

### `render_card(entry, active_tag) → str`

Builds the complete HTML for a single search result card.

| Parameter | Type | Description |
|---|---|---|
| `entry` | `dict` | Result dict with keys: `id`, `text`, `tags`, `tag_words` |
| `active_tag` | `str` | Passed through to `compute_highlights()` |

**Card structure:**

```html
<div class="result-card">
    <div class="result-id">        <!-- document ID -->
    <div class="result-text">      <!-- highlighted text from compute_highlights() -->
    <div class="tag-container">    <!-- tag pills, one per present tag -->
```

Tag pills use the CSS class pattern `tag-<tagname>` (e.g. `tag-ALL_CAPS`), which must be defined in `styles.css`.

**Returns:** HTML string for one result card.

---

### `render_bar_chart(tag_counts) → str`

Builds a pure HTML/CSS horizontal bar chart showing tag frequency across the current result set.

| Parameter | Type | Description |
|---|---|---|
| `tag_counts` | `dict` | Maps tag name → integer count of matching results |

**Chart features:**

- Bars are scaled relative to the highest tag count (`max_val`), with a minimum of 1 to avoid division by zero.
- Gridlines at 25%, 50%, 75%, and 100% provide consistent visual anchoring.
- Tick labels (`0%`, `25%`, `50%`, `75%`, `100%`) are rendered above the grid using absolute positioning.
- Bar colours are drawn from `BAR_COLORS`.
- Tag labels use `JetBrains Mono` monospace font, right-aligned in a fixed 160px column.
- Count values are overlaid on each bar in white bold text.

**Returns:** HTML string containing the full bar chart layout.

---

## CSS Class Dependencies

The following CSS classes must be present in `styles.css` for this module to render correctly:

| Class | Used by |
|---|---|
| `result-card` | `render_card()` — card container |
| `result-id` | `render_card()` — document ID label |
| `result-text` | `render_card()` — text body |
| `tag-container` | `render_card()` — tag pill row |
| `tag-<TAGNAME>` | `render_card()` — individual tag pills (one per tag) |
| `hl-orange`, `hl-red`, `hl-green`, `hl-blue`, `hl-purple` | `compute_highlights()` — highlighted word spans |
